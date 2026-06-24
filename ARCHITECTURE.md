# Smart-TIA — Architecture & Complete Functioning

> Deep technical documentation of the Smart Test Impact Analysis engine.
> For the short team summary and demo script, see [HANDOFF.md](HANDOFF.md).

---

## Table of contents
1. [What the system does](#1-what-the-system-does)
2. [High-level architecture](#2-high-level-architecture)
3. [End-to-end request flow](#3-end-to-end-request-flow)
4. [The selection engine (3 tiers)](#4-the-selection-engine-3-tiers)
5. [Backend module reference](#5-backend-module-reference)
6. [The bundled automotive demo](#6-the-bundled-automotive-demo)
7. [Requirements traceability (ISO 26262)](#7-requirements-traceability-iso-26262)
8. [Test levels & the time-saved metric](#8-test-levels--the-time-saved-metric)
9. [API reference](#9-api-reference)
10. [The dashboard payload (data contract)](#10-the-dashboard-payload-data-contract)
11. [Frontend reference](#11-frontend-reference)
12. [Caching, performance & safety](#12-caching-performance--safety)
13. [Repository layout](#13-repository-layout)
14. [Glossary](#14-glossary)

---

## 1. What the system does

Traditional CI runs the **entire** test suite on every commit, regardless of how
small the change is. That wastes time and compute.

**Smart-TIA** analyses a Git commit and runs **only the tests impacted by that
change**, then proves the saving is real and that no relevant test was skipped.

It answers the problem statement's evaluation criteria directly:

| Criterion | How Smart-TIA addresses it |
|---|---|
| Accuracy of test selection | Coverage-based mapping (observes real execution), per-test-case granularity |
| Reduce time without losing defect detection | Real measured timings + a regression demo that the reduced set catches + a full-run safety net |
| Integration with CI/CD & VCS | Clones any Git repo, diffs any commit (REST API; PR-trigger is the next step) |
| Scalability | Coverage map is built once per baseline and cached; selection is O(changed functions) |
| Demo clarity | A React dashboard with metrics, dependency trace, and requirements traceability |

---

## 2. High-level architecture

```
┌──────────────────────┐         HTTP / JSON          ┌──────────────────────────────┐
│  Frontend (React)    │  ─────────────────────────►  │  Backend (FastAPI)           │
│  Vite · port 5173    │  POST /api/analyze[/demo]    │  port 8000                   │
│  - InputForm         │  ◄─────────────────────────  │                              │
│  - Demo buttons      │     dashboard JSON payload   │  app/api/analyze.py          │
│  - Dashboard panels  │                              │        │                     │
└──────────────────────┘                              │        ▼                     │
                                                       │  app/services/pipeline.py    │
                                                       │   ├─ diff_analyzer  (AST)    │
                                                       │   ├─ coverage_mapper (cov)   │
                                                       │   ├─ test_mapper    (AST fb) │
                                                       │   ├─ test_runner    (pytest) │
                                                       │   └─ traceability   (ISO)    │
                                                       │        │                     │
                                                       │        ▼                     │
                                                       │   git clone (temp) + pytest  │
                                                       └──────────────────────────────┘
```

- **Frontend** is presentation only — it never touches Git. It sends a repo URL +
  commit (or a demo scenario) and renders whatever JSON it gets back.
- **Backend** does all the work: cloning, diffing, coverage mapping, running
  pytest, and assembling the metrics.

Technologies: **Python · FastAPI · GitPython · coverage.py · pytest (+ pytest-cov,
pytest-json-report)** on the backend; **React 19 · Vite · Tailwind · Recharts ·
lucide-react** on the frontend.

---

## 3. End-to-end request flow

What happens on a single analysis (see `app/services/pipeline.py::run_analysis`):

```
1.  git clone <repo> ─► a fresh temp dir (e.g. %TEMP%\smarttia_xxxx)
2.  resolve commits   ─► target = the commit to analyse
                         base   = its parent (or an explicit base_commit)
3.  DIFF (base..target) ─► diff_analyzer maps changed lines to enclosing
                           functions via the Python AST
                           e.g. {"src/battery_management.py": ["compute_soc"]}
4.  checkout BASELINE  ─► build/load the COVERAGE MAP:
                           run the whole suite once with per-test coverage
                           contexts → {(file, function): {tests that ran it}}
                           (cached on disk per baseline commit)
5.  SELECT             ─► intersect changed functions with the coverage map
                           → the impacted test node-ids
                           (or AST fallback, or full-run safety net)
6.  TRACEABILITY       ─► read @pytest.mark.req/level/asil from the target's
                           test files + load requirements.json
7.  checkout TARGET    ─► run the selected subset  (real pass/fail + time)
                           run the full suite       (baseline time + total count)
8.  BUILD PAYLOAD      ─► metrics, dependency trace, requirements, confidence
9.  cleanup            ─► close git handles, delete the temp clone
```

Everything is computed from a real clone and real pytest runs — **no number is
hard-coded**. The clone is deleted at the end (one-shot, nothing stored).

---

## 4. The selection engine (3 tiers)

The heart of the project. `pipeline._select()` chooses a strategy and decides
whether to engage the safety net.

### Tier 1 — COVERAGE (primary, the precision engine)
File: `app/services/coverage_mapper.py`

**Build phase** (`build_coverage_map`, run at the baseline commit):
1. Run `pytest --cov=src --cov-context=test`. The `--cov-context=test` flag tags
   every covered line with the **test that executed it**.
2. Read the `.coverage` database via the `coverage` API
   (`CoverageData.contexts_by_lineno`).
3. For each covered line, find its **enclosing function** using the file's AST.
4. Produce the map: `{"src/file.py::function": ["tests/x.py::test_a", ...]}`.

**Select phase** (`select_tests`):
- For each changed `(file, function)` from the diff, look up the tests that
  executed it in the map → those are the impacted tests (node-ids).

**Why it's better than text matching:** coverage records *actual runtime
execution*. If `test_compute_soc_*` calls `compute_soc()`, which internally calls
the shared helper `clamp()`, then the coverage map links those tests to
`sensor_utils.py::clamp`. So changing `clamp` correctly re-selects the battery
tests — **even though no test imports or names `sensor_utils`**. A text/AST
matcher cannot see that indirect link and would skip the bug. This is exactly
what the **"Hidden Bug"** demo scenario demonstrates.

### Tier 2 — AST (fallback)
File: `app/services/test_mapper.py`

Used when no coverage map can be built (e.g. analysing an external repo we can't
safely instrument). It parses each test file's AST and links a test to a changed
source file if the test **imports that module** or **references a changed
function name**. Fast and dependency-free, but only sees *direct* references.

### Tier 3 — FULL run (safety net)
Decided in `pipeline._select()`.

If confidence is low, Smart-TIA refuses to guess and runs the **entire suite**.
Triggers:
- a changed function/file can't be mapped to any test (e.g. brand-new untested
  code, or a config file), **or**
- the selection comes back empty.

This guarantees the tool never silently skips a defect — directly serving the
*"without compromising defect detection"* criterion. The **"Safety Net"** demo
scenario shows this.

---

## 5. Backend module reference

### `app/main.py`
Creates the FastAPI app, configures CORS for the Vite dev server, exposes
`GET /api/health`, and mounts the `auth` and `analyze` routers.

### `app/api/analyze.py`
- `POST /api/analyze` — analyse any Git repo (`repo_url`, `target_commit`,
  optional `base_commit`, `target_dir`, `tests_dir`). Delegates to
  `pipeline.run_analysis`.
- `POST /api/analyze/demo` — run a canned scenario against the bundled demo repo.
- `GET /api/analyze/demo/scenarios` — list available scenarios (drives the demo
  buttons). Auto-builds the demo repo on first use if missing.

### `app/api/auth.py`
Exchanges a GitHub OAuth `code` for an access token (optional; the demo doesn't
need it).

### `app/services/diff_analyzer.py`
`get_impacted_files(repo, base, target, target_dir)` → for each added/modified
file, returns the impacted functions:
- **Python files:** parses the AST of the *target* revision, records every
  function's line range, and maps each changed line (from the diff hunks) to its
  innermost enclosing function.
- **Other languages:** a regex fallback that scans upward from changed lines for
  a function signature.

### `app/services/coverage_mapper.py`
The coverage engine described in [§4](#4-the-selection-engine-3-tiers).
`build_coverage_map()` builds the function→tests map; `select_tests()` intersects
it with the diff and reports any `unmapped` changes (which drive the safety net).

### `app/services/test_mapper.py`
The Tier-2 AST fallback mapper (imports + referenced identifiers).

### `app/services/test_runner.py`
Runs pytest via `pytest-json-report` and parses the structured results.
- `run_full_suite()` — runs the whole `tests/` dir (the baseline).
- `run_selected()` — runs a list of files **or test node-ids** (per-test
  granularity). Returns per-test `status` + `duration_ms` (sum of
  setup/call/teardown) and a `passed` flag.

### `app/services/traceability.py`
- `extract_test_markers()` — statically parses `@pytest.mark.req/level/asil`
  decorators (and module-level `pytestmark`) from each test file's AST →
  `{nodeid: {req, level, asil}}`.
- `load_requirements_registry()` — reads `requirements.json` from the repo.
- `build_traceability()` — aggregates the impacted requirements for the selected
  tests and computes the highest ASIL touched.

### `app/services/pipeline.py`
The orchestrator. `run_analysis()` ties everything together (see
[§3](#3-end-to-end-request-flow)), `_select()` chooses the strategy
([§4](#4-the-selection-engine-3-tiers)), and `_build_payload()` assembles the
dashboard JSON ([§10](#10-the-dashboard-payload-data-contract)). It also caches
the coverage map per baseline commit under `backend/.tia_cache/`.

---

## 6. The bundled automotive demo

`app/demo/setup_demo.py` builds a self-contained Git repo at `backend/.demo_repo`
from the templates in `app/demo/codebase/`. It creates a clean baseline plus one
branch per scenario, each a **single, clean, one-file diff** off the baseline:

| Scenario | Branch | Change | Outcome |
|---|---|---|---|
| `safe` | `scenario/safe` | comment added inside `compute_soc` | 3 tests selected, all pass |
| `regression` | `scenario/regression` | SOC gain `*100` → `*10` | 3 tests selected, SOC test FAILS |
| `transitive` | `scenario/transitive` | `sensor_utils.clamp` lower bound dropped | coverage selects 3 battery tests, FAILS |
| `safety_net` | `scenario/safety-net` | new untested `pack_soc` function | unmappable → full suite runs |

The commit hashes are written to `.demo_repo/commits.json`, which the demo
endpoint reads.

**The ECU codebase** (`app/demo/codebase/src/`) is host-testable control logic
extracted from ECU firmware:
- `battery_management.py` — BMS: SOC estimation, charge interlock, cell balancing, thermal state
- `motor_controller.py` — torque limiting, RPM, regenerative braking
- `brake_system.py` — ABS: slip ratio, wheel-lock detection, pressure modulation
- `can_bus.py` — J1939-style signal encode/decode + frame checksum
- `diagnostics.py` — DTC validation, detection, severity
- `sensor_utils.py` — shared helpers (`clamp`, `moving_average`) used by the BMS

26 pytest cases live in `app/demo/codebase/tests/`.

---

## 7. Requirements traceability (ISO 26262)

Automotive software is requirement-driven and safety-classified. Every test is
tagged:

```python
pytestmark = pytest.mark.level("SIL")        # module-level test level

@pytest.mark.req("SR-BMS-001")               # software requirement ID
@pytest.mark.asil("C")                       # ASIL safety rating (A–D)
def test_compute_soc_midpoint():
    assert compute_soc(3.6) == 50.0
```

`requirements.json` is the registry mapping each requirement ID to a title, ASIL,
and component. At analysis time, Smart-TIA joins the selected tests → their
requirements → the registry, so the dashboard can show:

> **code change → impacted requirement(s) → tests → ASIL rating**

This is the chain a safety-critical V-model QA process cares about, and it is
surfaced as the **Requirements Impact** panel (highest ASIL touched, the list of
impacted requirements, and how many tests validate each).

---

## 8. Test levels & the time-saved metric

Each test declares an execution level, and `conftest.py` simulates a realistic
per-test latency for it:

| Level | Meaning | Simulated latency |
|---|---|---|
| `UNIT` | pure host logic | 0.05 s |
| `SIL` | Software-in-the-Loop (model settles) | 0.15 s |
| `HIL` | Hardware-in-the-Loop (firmware flashed to a bench) | 0.40 s |

This is **not faking the metric** — it models the genuine fact that HIL bench
tests are far more expensive than unit tests. Because the engine runs the suite
for real, the reported `standard_run_time` and `smart_run_time` are *measured*,
and skipping expensive HIL tests produces a proportionally larger saving. The
payload also reports `hil_tests_skipped / hil_tests_total` to highlight this.

`time_saved_percentage = (1 − smart_run_time / standard_run_time) × 100`.

---

## 9. API reference

### `POST /api/analyze`
Analyse an arbitrary Git repository.
```jsonc
// request
{
  "repo_url": "https://github.com/user/repo.git",
  "target_commit": "<sha or HEAD>",
  "base_commit": null,            // optional; defaults to target's parent
  "target_dir": "src/",           // where source lives
  "tests_dir": "tests"            // where tests live
}
```

### `POST /api/analyze/demo`
Run a canned scenario against the bundled ECU repo.
```jsonc
{ "scenario": "safe" }   // "safe" | "regression" | "transitive" | "safety_net"
```

### `GET /api/analyze/demo/scenarios`
Returns the scenario list (label + expectation) used to render the demo buttons.

### `GET /api/health`
Liveness check: `{ "status": "ok", "service": "SmartTIA Engine" }`.

Both analyse endpoints return the **dashboard payload** below.

---

## 10. The dashboard payload (data contract)

```jsonc
{
  "pipeline_run": {
    "commit_hash": "9b08615",
    "commit_message": "perf(bms): tweak SOC interpolation gain",
    "base_commit": "31e441a",
    "timestamp": "Just now",
    "status": "failed"                 // "success" | "failed"
  },
  "metrics": {
    "total_tests_in_suite": 26,
    "tests_executed": 3,
    "tests_skipped": 23,
    "standard_run_time_seconds": 5.8,
    "smart_run_time_seconds": 0.55,
    "time_saved_percentage": 90.7,
    "hil_tests_total": 11,
    "hil_tests_skipped": 11
  },
  "analysis": {
    "selection_method": "coverage",    // "coverage" | "ast" | "full-fallback"
    "confidence": "high",              // "high" | "low"
    "fallback_reason": null,
    "modified_files": ["src/battery_management.py"],
    "impacted_functions": ["src/battery_management.py::compute_soc"],
    "selected_tests": ["tests/test_battery_management.py::test_compute_soc_midpoint", "..."],
    "all_selected_passed": false
  },
  "traceability": {
    "impacted_requirements": [
      { "id": "SR-BMS-001", "title": "Battery SOC estimation accuracy",
        "asil": "C", "component": "Battery Management", "tests": ["..."] }
    ],
    "highest_asil": "C"
  },
  "dependency_trace": [
    {
      "modified_file": "src/battery_management.py",
      "impacted_tests": [
        { "test_name": "test_compute_soc_midpoint", "status": "failed",
          "duration_ms": 152, "level": "SIL", "asil": "C", "requirement": "SR-BMS-001" }
      ]
    }
  ],
  "scenario": {                         // only present for /demo
    "key": "regression", "label": "Inject regression", "expectation": "..."
  }
}
```

---

## 11. Frontend reference

`frontend/src/`:
- **`App.jsx`** — state + API calls (`/api/analyze`, `/api/analyze/demo`), the 4
  demo buttons, error banner, scenario banner, and the dashboard layout.
- **`components/InputForm.jsx`** — repo URL + commit hash input for real repos.
- **`components/GithubAuthGuard.jsx`** — OAuth gate with a "Continue in demo mode"
  bypass.
- **`components/Dashboard/Header.jsx`** — commit summary + pipeline status.
- **`components/Dashboard/KPIs.jsx`** — time-saved %, execution time, suite efficiency.
- **`components/Dashboard/RequirementsImpact.jsx`** — selection method, confidence,
  highest ASIL, HIL tests avoided, impacted requirements (ISO 26262 panel).
- **`components/Dashboard/Charts.jsx`** — time comparison bar + executed/skipped donut (Recharts).
- **`components/Dashboard/DependencyTrace.jsx`** — modified file → impacted tests,
  each with status, duration, level, requirement, and ASIL badges.
- **`components/EmptyState.jsx` / `LoadingState.jsx`** — idle and progress views.

The dashboard components consume the JSON contract in
[§10](#10-the-dashboard-payload-data-contract) directly.

---

## 12. Caching, performance & safety

- **Coverage-map cache** (`backend/.tia_cache/`): the map is keyed by
  `(repo_source, baseline_commit)`. Since a commit is immutable, the map is built
  once and reused on subsequent analyses of the same baseline — so repeated demos
  are fast. Rebuild the demo repo (new commits) ⇒ new key ⇒ rebuilt automatically.
- **Temp clones**: every analysis clones to a fresh temp dir and deletes it in a
  `finally` block. On Windows, Git marks `.git` files read-only, so cleanup uses a
  force-remove helper that clears the read-only bit (also used by `setup_demo`).
- **One-shot / no storage**: nothing about the analysed repo is persisted beyond
  the cached coverage map of the *baseline*.
- **Safety first**: low-confidence changes always fall back to a full run.

---

## 13. Repository layout

```
4pm-chai-lovers/
├─ HANDOFF.md                     ← team summary + demo script
├─ ARCHITECTURE.md                ← this document
├─ Readme.md
├─ backend/
│  ├─ requirements.txt
│  ├─ .gitignore                  ← ignores venv, .demo_repo, .tia_cache, __pycache__
│  └─ app/
│     ├─ main.py                  ← FastAPI app + routers
│     ├─ api/
│     │  ├─ analyze.py            ← /api/analyze + /api/analyze/demo
│     │  └─ auth.py               ← GitHub OAuth (optional)
│     ├─ core/config.py           ← env config (GitHub creds)
│     ├─ schemas/
│     │  ├─ analyze.py            ← request models
│     │  └─ auth.py
│     ├─ services/                ← THE ENGINE
│     │  ├─ pipeline.py           ← orchestrator (clone→map→select→run→payload)
│     │  ├─ diff_analyzer.py      ← AST diff → impacted functions
│     │  ├─ coverage_mapper.py    ← coverage map + selection (Tier 1)
│     │  ├─ test_mapper.py        ← AST mapping (Tier 2 fallback)
│     │  ├─ test_runner.py        ← pytest execution + metrics
│     │  └─ traceability.py       ← ISO 26262 requirements/ASIL
│     └─ demo/
│        ├─ setup_demo.py         ← builds .demo_repo (baseline + scenario branches)
│        └─ codebase/             ← templates copied into the demo repo
│           ├─ src/               ← ECU modules (BMS, motor, brake, CAN, diag, utils)
│           ├─ tests/             ← 26 tagged pytest cases
│           ├─ conftest.py        ← level-based latency fixture
│           ├─ pytest.ini         ← marker registration
│           └─ requirements.json  ← requirements registry
│  ├─ .demo_repo/                 ← generated demo git repo (gitignored)
│  └─ .tia_cache/                 ← cached coverage maps (gitignored)
└─ frontend/
   ├─ package.json
   └─ src/
      ├─ App.jsx                  ← API calls + dashboard layout
      └─ components/
         ├─ InputForm.jsx, GithubAuthGuard.jsx, EmptyState.jsx, LoadingState.jsx
         └─ Dashboard/
            ├─ Header.jsx, KPIs.jsx, Charts.jsx
            ├─ RequirementsImpact.jsx
            └─ DependencyTrace.jsx
```

---

## 14. Glossary

- **TIA (Test Impact Analysis):** selecting the subset of tests affected by a code change.
- **Coverage context:** coverage.py feature that records *which test* executed each line.
- **Transitive dependency:** A test exercises function B which internally calls
  changed function A — the test depends on A indirectly.
- **ISO 26262 / ASIL:** automotive functional-safety standard; ASIL A–D rate how
  safety-critical a requirement is (D = most critical).
- **SIL / HIL:** Software-in-the-Loop / Hardware-in-the-Loop test levels; HIL runs
  against (simulated) hardware and is slow/expensive.
- **DTC:** Diagnostic Trouble Code (e.g. `P0AFA`).
- **Safety net / full fallback:** running the entire suite when impact can't be
  confidently determined.
```
