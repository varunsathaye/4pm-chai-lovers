# SmartTIA Engine — Backend Architecture

## What it is

A **FastAPI server** that implements **Test Impact Analysis (TIA)** for automotive-grade Python codebases. Instead of running every test on every commit (slow, expensive), it figures out *exactly which tests are affected by a code change* and runs only those.

---

## High-level flow

```
POST /api/analyze  (repo_url, target_commit, base_commit)
         │
         ▼
  Clone repo → base..target diff (AST-level) → build/load coverage map
         → select impacted tests → safety fallback check → run tests
         → requirements traceability → return dashboard payload
```

---

## Key components

### `app/main.py`
FastAPI app entry point. Mounts two routers under `/api/auth` and `/api/analyze`, enables CORS for `localhost:5173` (Vite frontend).

### `app/core/config.py`
Loads `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` from `.env` for OAuth.

### `app/api/auth.py` (`POST /api/auth/github`)
Exchanges a temporary GitHub OAuth code for an access token. Simple pass-through proxy to GitHub's OAuth endpoint.

### `app/api/analyze.py` — 3 endpoints:
| Endpoint | Purpose |
|---|---|
| `POST /api/analyze` | Run TIA on **any** Git repo (URL + commit range) |
| `POST /api/analyze/demo` | Run one of 4 canned scenarios on the bundled ECU demo repo |
| `GET /api/analyze/demo/scenarios` | List available demo scenarios for the UI |

### `app/schemas/analyze.py`
Pydantic models for `AnalyzeRequest` (repo_url, target_commit, base_commit, target_dir, tests_dir) and `DemoRequest` (scenario name).

---

## Services (the engine room)

### `pipeline.py` — Orchestrator
The master controller. Flow:
1. Clone the repo to a temp dir
2. Resolve base commit (auto = parent of target)
3. **Diff analysis**: `base..target` → list of changed files + impacted functions (AST-level)
4. Checkout base → **build/load coverage map** from cache (hashed by `repo@base_sha`)
5. **Select tests** via coverage map (or AST fallback if no coverage data)
6. **Safety net**: if zero tests selected or unmapped changes exist → fall back to running the **full suite**
7. **Traceability**: extract `@pytest.mark.req/level/asil` markers + join with `requirements.json`
8. Checkout target → run **full suite** (baseline) + **smart suite** (only selected tests)
9. Build the dashboard payload with metrics (time saved, HIL skipped, etc.)

### `diff_analyzer.py` — What changed?
Uses GitPython to diff `base..target`. For each modified `.py` file:
- Parses the **real Python AST** of the target revision
- Maps each changed line to its innermost enclosing function/method
- Returns `[{file, change_type, impacted_functions: [...]}]`

For non-Python files, falls back to a regex-based function scanner.

### `coverage_mapper.py` — The precision engine
The **gold standard** approach:
1. At the baseline commit, runs the full test suite with `pytest --cov --cov-context=test`
2. Builds a map of `(source_file::function_name) → { test_nodeids }` based on what actually executed at runtime
3. **Caches** this map on disk per baseline commit
4. `select_tests()` matches changed functions against the map to pick exactly the tests that touched those functions

This catches **transitive/indirect** dependencies — e.g. a test calls `compute_soc()` which internally calls `clamp()` from `sensor_utils.py`; changing `clamp()` correctly re-selects the battery tests, even though no test file mentions `sensor_utils`.

### `test_mapper.py` — AST fallback
Used when coverage data isn't available. Parses test files' AST to find:
- Which modules they import
- Which identifiers they reference

Then matches these against the changed files/functions. A whole-word regex fallback catches module-level changes.

### `test_runner.py` — Execution
Runs pytest with `--json-report` to get structured results (per-test outcome + duration). Two modes:
- `run_full_suite()` — runs `tests/` completely (baseline cost measurement)
- `run_selected()` — runs only specific test files or nodeids

Simulated per-test latency via `conftest.py` bench fixture (UNIT: 50ms, SIL: 150ms, HIL: 400ms).

### `traceability.py` — ISO 26262 / ASIL
Reads pytest markers (`@pytest.mark.req`, `.level`, `.asil`) from test file ASTs, joins with `requirements.json` from the repo root, and builds an "impacted requirements" block showing which safety-critical requirements each selected test covers. Returns the highest ASIL level among impacted requirements.

---

## Demo system (`app/demo/`)

### `setup_demo.py`
Builds a self-contained automotive ECU git repo under `backend/.demo_repo` with 4 scenario branches:

| Scenario | What happens | Expected outcome |
|---|---|---|
| **safe** | Docstring refactor in `compute_soc` | 3 battery tests re-run, all pass |
| **regression** | SOC gain corrupted (100→10) | SOC test catches the bug |
| **transitive** | `clamp()` helper broken in `sensor_utils.py` | Coverage map re-selects battery tests; text matching would miss this |
| **safety-net** | New `pack_soc()` function added with no tests | No mapping found → full suite runs (safety fallback) |

### Demo codebase
A simulated EV ECU with modules: `battery_management`, `motor_controller`, `brake_system`, `can_bus`, `diagnostics`, `sensor_utils`. Tests are marked with requirement IDs (e.g. `SR-BMS-001`), test levels (`UNIT`/`SIL`/`HIL`), and ASIL ratings (`A`-`D`). A `requirements.json` registry maps requirement IDs to titles and safety classifications.

---

## Standalone scripts (`scripts/`)
Earlier versions of `diff_analyzer.py` and `test_mapper.py` that work at the file level (regex-based C++ scanning, keyword search) — these are prototypes superseded by the AST-based services.

---

## In summary
This is a **test impact analysis engine** purpose-built for safety-critical automotive software. It uses runtime coverage data (not just text matching) to precisely select the minimum set of tests affected by a code change, integrates with ISO 26262 requirements traceability, and intelligently falls back to the full suite when confidence is low — all exposed through a REST API for a dashboard UI.
