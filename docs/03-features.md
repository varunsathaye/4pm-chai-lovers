# Feature Documentation

## 1. 3-Tier Selection Engine

The core intellectual property of SmartTIA is its **3-tier selection strategy**, implemented in `pipeline._select()`. Each tier has different capabilities, and the system falls through tiers when data is unavailable.

### Tier 1: Coverage-Based Selection (Precision Engine)

**How it works:**

1. At the **baseline commit**, the system runs `pytest --cov=<source_dir> --cov-context=test` against every test file.
2. The `coverage.py` API provides `contexts_by_lineno` — a mapping from each source line number to the list of test nodeids that executed it.
3. An AST-based function range analyzer (`_function_ranges()`) maps line numbers to enclosing function names.
4. The result is a map: `{"src/file.py::function_name": ["tests/test_file.py::test_func", ...]}`.
5. This map is serialized and cached to `backend/.tia_cache/`.

**Selection phase:** For each changed `(file, function)` from the diff analyzer, the coverage map is consulted. All tests that touched the changed function are selected.

**What this catches that other methods miss:** **Transitive/indirect dependencies.** If test T calls function A, which internally calls changed helper B, the coverage map records that T executed line N of function B at runtime. Text-based matchers would miss this entirely because no test file textually references B.

**Caching:** Coverage maps are cached by `sha1(repo_source + "@" + base_sha)`. Stale entries (with `ok: True` but empty data) are automatically discarded on read.

### Tier 2: AST Static Mapping Fallback

**When triggered:** When no coverage map exists (e.g., external repo, non-instrumentable codebase).

**How it works:**

The `test_mapper.py` service parses every test file to find what symbols and modules it references, then matches them against the changed files from the diff.

| Language | Method | Details |
|----------|--------|---------|
| Python | AST analysis | Parses `import X`, `from X import Y`, all `ast.Name` identifiers |
| C/C++ | Regex | Extracts `#include "path/file.h"`, function calls, identifiers |
| Other | Regex fallback | Extracts filenames from include/import statements + whole-word keyword scan |

For each changed source file, the mapper:
1. Extracts the filename stem (e.g., `battery_manager` from `src/battery_manager.cpp`)
2. Checks if any test file imports or references that stem
3. For Python: also checks function-level identifiers via AST
4. Falls back to a whole-word keyword regex scan to ensure no test is missed

**Cross-file call-chain analysis** (`diff_analyzer._find_cross_file_callers()`):
- Scans all source files under `target_dir` for call sites referencing changed functions
- Adds indirect entries with `change_type: "I"` so the mapper also selects tests for files that CALL changed functions (not just the files where the change occurred)

### Tier 3: Full Suite Fallback (Safety Net)

**When triggered:** When confidence is low:
- Zero tests were selected by Tiers 1 or 2
- Some changed source items could not be mapped to any test

**Behavior:** The entire test suite is executed, guaranteeing the system never silently misses a regression. The dashboard shows the fallback reason.

## 2. Diff Analysis System

The `diff_analyzer.py` service performs git diff analysis with multi-language support.

### Git Diff Processing

1. Gets raw diff between base and target commits
2. Extracts added/modified hunks with line numbers
3. Filters to only files under `target_dir` (configurable, default `src/`)

### Function-Level Impact Detection

**Python files:** Uses the `ast` module to build a complete function range map:
- Traverses the AST to find all `FunctionDef`, `AsyncFunctionDef`, and `ClassDef` nodes
- Records `(qualified_name, start_line, end_line)` for each
- Maps each changed line to its innermost enclosing function
- Handles nested classes and functions with dot-separated qualified names

**Non-Python files:** Uses regex to detect function/method signatures:
- Pattern: optional return type, function name, parameter list in parentheses, optional trailing keywords (`override`, `const`, `noexcept`, `final`)
- Skips member-access calls (lines containing `.`, `->`, or `::`)
- Skips lines starting with known keywords (`if`, `while`, `for`, `return`, `def`, etc.)

### Cross-File Caller Detection

For each function identified as changed:
1. Scans every source file under `target_dir` for call sites
2. Identifies the enclosing function around each call site
3. Records indirect entries so the test mapper selects tests for files that USE the changed function

## 3. Requirements Traceability (ISO 26262)

Designed for automotive and safety-critical software development, the traceability module connects code changes to requirements and safety classifications.

### Test Markers

Tests are annotated with pytest markers in three ways:

**Function-level decorators:**
```python
@pytest.mark.req("SR-BMS-001")
@pytest.mark.asil("C")
def test_soc_estimation():
    ...
```

**Module-level assignments:**
```python
pytestmark = [
    pytest.mark.level("SIL"),
    pytest.mark.req("SR-BMS-001"),
]
```

### Supported Markers

| Marker | Purpose | Example Values |
|--------|---------|---------------|
| `@pytest.mark.req("ID")` | Requirement ID | `SR-BMS-001`, `SR-MOT-002` |
| `@pytest.mark.level("LVL")` | Test execution level | `UNIT`, `SIL`, `HIL` |
| `@pytest.mark.asil("LVL")` | Safety integrity level | `QM`, `A`, `B`, `C`, `D` |

### ASIL Ordering

```
QM (Quality Managed) < A < B < C < D
```

The dashboard displays the **highest ASIL** touched by the selected tests, as well as each requirement's ASIL rating.

### Requirements Registry

A `requirements.json` file in the repo root (optional) contains the formal requirements catalog:

```json
{
  "SR-BMS-001": {
    "title": "Battery State of Charge Estimation",
    "asil": "C",
    "component": "BMS"
  }
}
```

### Dashboard Display

The `RequirementsImpact` component shows:
- **Selection method** (Coverage-based, AST static, or Safety fallback)
- **Confidence level** (High/Low) with visual indicator
- **Highest ASIL touched** with color-coded badge
- **HIL/SIL tests avoided** count
- **Safety net engaged** warning when applicable
- **Impacted software requirements** list with ID, title, component, ASIL, and test count

## 4. Time-Saved Metrics

The system measures and displays its own effectiveness:

### Calculation

```
time_saved_percentage = (1 - smart_run_time / standard_run_time) * 100
```

### Data Sources

1. **Actual pytest execution:** `test_runner.py` measures real test duration from `pytest-json-report` output (setup + call + teardown phase durations)
2. **Test timings file:** Non-Python repos can include a `test_timings.json` in the tests directory mapping each test file to its expected duration in seconds
3. **Simulated latency (demo):** The demo conftest includes a `bench` fixture that adds latency per test level:
   - UNIT: 50ms
   - SIL: 150ms
   - HIL: 400ms

### Dashboard Display

| Metric | Location | Format |
|--------|----------|--------|
| Time saved | KPI card | Big percentage number (e.g., 87.8%) |
| Smart run time | KPI card | `Xs` with original strikethrough |
| Tests executed | KPI card | `N / M tests` |
| Tests skipped | KPI card | `N test(s) skipped safely` |
| Suite avoidance | Pie chart | Executed vs Skipped (donut) |
| Time comparison | Bar chart | Standard CI vs Smart TIA (horizontal bars) |
| HIL tests avoided | Requirements panel | Count of expensive HIL tests not run |

## 5. GitHub OAuth Integration

### Flow

1. User clicks "Connect with GitHub" → redirected to `https://github.com/login/oauth/authorize`
2. User authorizes the app → GitHub redirects to `/auth/callback?code=...`
3. Frontend `GithubCallback` component displays a terminal-style handshake screen
4. Backend `POST /api/auth/github` exchanges the code for an access token via GitHub API
5. Backend returns the access token; frontend fetches GitHub user profile (login, avatar)
6. Token and user info are saved to `localStorage` for persistence across page reloads
7. Token is passed to the analysis endpoints for private repo cloning

### Private Repository Support

When a `github_token` is provided, the backend rewrites the clone URL:
```
https://github.com/owner/repo.git
→ https://x-access-token:{token}@github.com/owner/repo.git
```

### Persistence

- Token and user info are stored in `localStorage`
- On app load, the system checks for existing credentials and auto-authenticates
- A **ProfileMenu** component in the navbar shows the user's avatar and provides a logout button

### UI Components

| Component | Function |
|-----------|----------|
| `GithubAuthGuard` | Route guard, redirects unauthenticated users to login |
| `GithubCallback` | Terminal-style OAuth handshake animation |
| `ProfileMenu` | Avatar + dropdown with sign-out option |
| `Navbar` | Top bar with SmartTIA branding + ProfileMenu |

## 6. All Test Files Overview

The Dependency Trace section of the dashboard shows a complete view of the test suite:

- **All test files** are displayed as labeled pills at the top of the section
- **Selected files** (impacted by the change) are highlighted with green borders and a checkmark badge
- **Non-selected files** are shown in muted styling
- A counter shows `X / Y selected`
- Below the overview, each modified source file is shown with its specific impacted tests

## 7. Demo System

See [04-demo-system.md](./04-demo-system.md) for full documentation of the demo system, including all 5 test files, 6 source modules, and 4 scenarios.

## 8. API Reference

See [05-api-reference.md](./05-api-reference.md) for complete API endpoint documentation.

## 9. Cross-Language Support

### Test File Detection

The system recognizes test files by extension across 10+ languages:

| Category | Extensions |
|----------|-----------|
| Python | `.py` |
| C/C++ | `.c`, `.cc`, `.cpp`, `.cxx`, `.h`, `.hpp`, `.hxx` |
| JavaScript/TypeScript | `.js`, `.ts`, `.jsx`, `.tsx` |
| Java/Kotlin | `.java`, `.kt` |
| Go | `.go` |
| Rust | `.rs` |
| Ruby | `.rb` |
| Swift | `.swift` |
| Shell | `.sh`, `.bash` |

### Language-Specific Analysis

| Language | Diff Analysis | Test Mapping |
|----------|--------------|-------------|
| Python | Full AST (function ranges, nested classes) | AST (imports, identifiers) |
| C/C++ | Regex (signatures, `override`/`const`/`noexcept`/`final` keywords) | Regex (`#include`, identifiers) |
| Other | Regex (generic function detection) | Regex (import/include, keyword scan) |

## 10. Non-Python Repository Support

When a repository has no Python test files:

1. **Coverage maps** are not built (`coverage_mapper` returns `ok: False`)
2. **Diff analysis** still works (regex-based for non-Python files)
3. **Test mapping** uses regex-based include/identifier extraction
4. **Test execution is skipped** — no pytest is called
5. **Mock test entries** are created from the AST mapping for dashboard display
6. **Test timings** are read from `test_timings.json` (if present) to compute time-saved metrics
7. **All test files** are discovered and counted for the suite overview
