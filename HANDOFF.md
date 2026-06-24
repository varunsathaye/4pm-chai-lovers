# Smart-TIA — Team Handoff & Change Log

**Team:** 4PM Chai Lovers · **PS:** MergeRequest-based Test Case Execution (SSDV / DevOps)

This is the team-facing summary. For a deep dive into how every part works, see
[ARCHITECTURE.md](ARCHITECTURE.md).

---

## 1. TL;DR — what we built

A real **Test Impact Analysis (TIA)** engine that, for any commit, runs only the
tests actually affected by the change — and proves it didn't skip anything that
matters.

- **Before:** the dashboard showed hard-coded fake numbers; the backend only did
  GitHub login.
- **Now:** a real pipeline — **clone → coverage-based impact map → select only
  impacted tests → run them + a full baseline → 100% real metrics** — wired end
  to end to the dashboard, plus an automotive ECU test suite with ISO 26262
  requirements traceability.

The selection engine is **coverage-based** (it observes what each test actually
executes), which catches *indirect/transitive* dependencies that simple
text/AST matching would miss — and it falls back to a **full run** whenever it
is not confident, so a defect can never silently slip through.

---

## 2. The demo (this is what we present)

Four buttons run against the bundled **automotive ECU codebase** (26 tests across
5 modules: BMS, motor, brake, CAN, diagnostics):

| Button | Simulated change | Result | What it proves |
|---|---|---|---|
| 🟢 **Safe Refactor** | harmless edit to `compute_soc` | 3/26 tests, ~92% time saved, all green | precise selection + time saved |
| 🔴 **Inject Regression** | bug in `compute_soc` | 3/26 tests, **one FAILS — bug caught** | defect detection |
| 🟣 **Hidden Bug** | bug in shared `sensor_utils.clamp` (no test references it) | coverage still selects the 3 battery tests, **bug caught** | **coverage beats text matching** |
| 🟡 **Safety Net** | brand-new untested function | runs the **full suite** (low confidence) | never skips when unsure |

**Headline line for judges:** *"We run a fraction of the tests, save ~90% of the
time, and still catch the regression a full run would catch — including bugs in
shared code that no test mentions. And when we're not sure, we run everything."*

That maps 1:1 onto the evaluation criteria: *accuracy of selection* and
*reduction in time without compromising defect detection*.

---

## 3. How to run it

### Backend (FastAPI, port 8000)
```bash
cd backend
python -m venv venv
venv\Scripts\activate              # source venv/bin/activate on Linux/Mac
pip install -r requirements.txt    # includes coverage + pytest-cov

python -m app.demo.setup_demo      # ONE-TIME: builds the bundled demo git repo
uvicorn app.main:app --reload
```

### Frontend (React + Vite, port 5173)
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 → **"Continue in demo mode →"** → click any demo button.

> GitHub OAuth still works if `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` are set
> in `backend/.env`, but **demo mode bypasses login** so the demo never depends
> on it.

**Demo-day reset (always do this before presenting):**
```bash
cd backend && python -m app.demo.setup_demo   # clean, repeatable reset
uvicorn app.main:app --reload
```

---

## 4. Selection strategy (3 tiers)

1. **COVERAGE** (primary) — tests whose runtime coverage touched a changed
   function. Per-test-case granularity; catches transitive dependencies.
2. **AST** (fallback) — direct import/symbol matching, used when a coverage map
   can't be built (e.g. an external repo we can't safely instrument).
3. **FULL** (safety net) — runs everything when confidence is low (a change can't
   be mapped, touches config, or selects zero tests).

---

## 5. What changed, file by file

### Backend — analysis engine (`backend/app/services/`)
- **`coverage_mapper.py`** *(new)* — builds the coverage map at the baseline and
  selects impacted tests. The precision core.
- **`traceability.py`** *(new)* — reads requirement / level / ASIL markers from
  test files and joins them with `requirements.json`.
- **`pipeline.py`** — orchestrates clone → map → select (3-tier) → run →
  traceability → payload. Caches the coverage map per baseline commit.
- **`test_runner.py`** — runs individual test node-ids (per-test granularity) and
  captures real timings via `pytest-json-report`.
- **`diff_analyzer.py`** — AST diff: maps changed lines to enclosing functions.
- **`test_mapper.py`** — static AST mapper (used as the fallback strategy).

### Backend — API (`backend/app/`)
- **`api/analyze.py`** — `POST /api/analyze` (any repo), `POST /api/analyze/demo`
  (canned scenarios), `GET /api/analyze/demo/scenarios`.
- **`api/auth.py`** — GitHub OAuth code exchange (optional).
- **`main.py`** — registers routers + `/api/health`.

### Backend — bundled demo (`backend/app/demo/`)
- **`codebase/src/`** — ECU control logic: `battery_management`, `motor_controller`,
  `brake_system`, `can_bus`, `diagnostics`, `sensor_utils` (shared helper).
- **`codebase/tests/`** — 26 pytest cases tagged with `req`/`level`/`asil` markers.
- **`codebase/conftest.py`** — per-test latency by level (UNIT/SIL/HIL).
- **`codebase/requirements.json`** — the requirements registry (ISO 26262).
- **`setup_demo.py`** — builds the demo git repo: a clean baseline + one branch
  per scenario (safe / regression / transitive / safety_net).

### Frontend (`frontend/src/`)
- **`App.jsx`** — calls the real API, 4 demo buttons, scenario banner, error handling.
- **`components/Dashboard/RequirementsImpact.jsx`** *(new)* — selection method,
  confidence, highest ASIL, HIL tests avoided, impacted requirements.
- **`components/Dashboard/DependencyTrace.jsx`** — per-test level/requirement/ASIL badges.
- **`KPIs.jsx`, `Charts.jsx`, `Header.jsx`** — metric cards & charts (unchanged shape).
- **`GithubAuthGuard.jsx`** — adds a "Continue in demo mode" bypass.

---

## 6. Known limitations / next steps
- **MR/CI integration (P2)** not yet built — a GitHub Action that runs the engine
  on every PR and posts the impact summary. This is the next big win and makes it
  literally "MergeRequest based".
- Coverage map is rebuilt when the baseline commit changes; for very large repos
  you'd update it incrementally instead of rebuilding.
- Non-Python repos get diff + AST mapping but not pytest execution metrics.

---

## 7. 5-minute demo script
1. Open dashboard → "Continue in demo mode".
2. **Safe Refactor** → 3/26 tests, ~92% saved, all green, traces to SR-BMS-001 (ASIL C).
3. **Inject Regression** → same 3 tests, one **red**: *"fewer tests, less time, bug still caught."*
4. **Hidden Bug** → change a shared helper no test mentions; coverage still catches it: *"text matching would've skipped this."*
5. **Safety Net** → untested change → full run: *"when we're not sure, we never skip."*
6. (Optional) paste a real GitHub repo URL + commit into the form to show it's not hardcoded.
