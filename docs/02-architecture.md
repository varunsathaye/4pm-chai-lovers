# System Architecture

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Backend Runtime | Python 3 | 3.x | Core engine |
| API Framework | FastAPI | — | REST endpoints |
| Source Control | GitPython | — | Repo cloning, diff, checkout |
| Test Framework | pytest | ≥7.0 | Test execution |
| Coverage | pytest-cov + coverage.py | ≥7.0 | Runtime line-coverage tracking |
| Test Reporting | pytest-json-report | — | Structured test result output |
| Frontend Runtime | React | 19.x | Dashboard UI |
| Build Tool | Vite | — | Dev server + bundling |
| CSS Framework | Tailwind CSS | 4.x | Styling |
| Charts | Recharts | 3.x | Visualizations |
| Icons | lucide-react | — | Icon library |
| Animations | framer-motion | — | UI transitions |

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        User / Browser                               │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              React SPA (Vite dev :5173)                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────┐  │   │
│  │  │InputForm │ │ Navbar   │ │ Dashboard │ │ AuthGuard    │  │   │
│  │  │          │ │Profile   │ │ KPIs      │ │ GithubCallback│  │   │
│  │  │          │ │          │ │ Charts    │ │              │  │   │
│  │  │          │ │          │ │ DepTrace  │ │              │  │   │
│  │  └──────────┘ └──────────┘ └───────────┘ └──────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────────┘
                         │ HTTP (JSON)
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 FastAPI Backend (:8000)                              │
│                                                                      │
│  ┌────────────┐  ┌──────────────────────────────────────────────┐   │
│  │ Auth Router│  │              Analyze Router                   │   │
│  │  POST /auth│  │  POST /analyze     POST /analyze/map         │   │
│  │  /github   │  │  POST /analyze/demo  GET /analyze/demo/      │   │
│  └────────────┘  │                       /scenarios              │   │
│                  └──────────────┬───────────────────────────────┘   │
│                                 │                                   │
│                  ┌──────────────▼───────────────────────────────┐   │
│                  │              Services Layer                   │   │
│                  │  ┌──────────┐ ┌──────────┐ ┌─────────────┐  │   │
│                  │  │ Pipeline │ │  Diff    │ │  Coverage   │  │   │
│                  │  │(Orchestr)│ │ Analyzer │ │  Mapper     │  │   │
│                  │  ├──────────┤ ├──────────┤ ├─────────────┤  │   │
│                  │  │Test      │ │ Test     │ │ Traceability│  │   │
│                  │  │Mapper    │ │ Runner   │ │ (ISO 26262) │  │   │
│                  │  ├──────────┤ ├──────────┤ ├─────────────┤  │   │
│                  │  │Timing    │ │ Simple   │ │             │  │   │
│                  │  │Service   │ │ Mapper   │ │             │  │   │
│                  │  └──────────┘ └──────────┘ └─────────────┘  │   │
│                  └──────────────────────────────────────────────┘   │
│                                 │                                   │
│                  ┌──────────────▼───────────────────────────────┐   │
│                  │         External Systems                     │   │
│                  │  ┌──────────┐ ┌──────────┐ ┌─────────────┐  │   │
│                  │  │   Git    │ │  pytest  │ │  GitHub     │  │   │
│                  │  │  Remote  │ │         │ │  OAuth API  │  │   │
│                  │  └──────────┘ └──────────┘ └─────────────┘  │   │
│                  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow — Full Analysis Pipeline

```
User clicks "Analyze Impact"
         │
         ▼
POST /api/analyze { repo_url, target_commit, base_commit?, ... }
         │
         ▼
pipeline.run_analysis()
         │
         ├── 1. Clone repository (with GitHub token for private repos)
         │
         ├── 2. Resolve base commit (parent or explicit)
         │
         ├── 3. Diff analysis (base..target)
         │       └── diff_analyzer.get_impacted_files()
         │           ├── Python: AST-based function-range mapping
         │           └── Other: regex function signature matching
         │           └── Cross-file call-chain detection
         │
         ├── 4. Checkout baseline commit
         │
         ├── 5. Build/load coverage map
         │       └── coverage_mapper.build_coverage_map()
         │           └── pytest --cov --cov-context=test
         │           └── Cache to .tia_cache/
         │
         ├── 6. Select impacted tests (3-tier)
         │       ├── Tier 1: coverage_mapper.select_tests()
         │       ├── Tier 2: test_mapper.map_tests() (AST static)
         │       └── Tier 3: full suite fallback
         │
         ├── 7. Extract traceability markers
         │       └── traceability.extract_test_markers()
         │       └── traceability.load_requirements_registry()
         │
         ├── 8. Checkout target commit
         │
         ├── 9. Execute tests
         │       ├── test_runner.run_full_suite() [standard]
         │       └── test_runner.run_selected()   [smart]
         │
         ├── 10. Override timings from test_timings.json (if present)
         │
         └── 11. Build dashboard payload
                 └── _build_payload() → JSON response
```

## Caching Architecture

Coverage maps are expensive to build (requires full test execution at the baseline commit). Results are cached to avoid rebuilding on repeated runs:

```
Cache key:   sha1("<repo_source>@<base_sha>")[:16]
Cache file:  backend/.tia_cache/covmap_<hash>.json
Cache TTL:   Indefinite (manual purge by deleting .tia_cache/)
Stale guard: Entries with ok=True but empty by_function/covered_files are auto-discarded
```

## Directory Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI entry point, CORS, router mounting
│   ├── core/config.py             # Environment variable loading
│   ├── api/
│   │   ├── analyze.py             # POST /analyze, /analyze/map, /analyze/demo
│   │   └── auth.py                # POST /auth/github (OAuth code exchange)
│   ├── schemas/
│   │   ├── analyze.py             # Pydantic models: AnalyzeRequest, MapRequest, DemoRequest
│   │   └── auth.py                # AuthRequest model
│   ├── services/
│   │   ├── pipeline.py            # End-to-end orchestrator
│   │   ├── diff_analyzer.py       # AST/regex diff analysis
│   │   ├── coverage_mapper.py     # Coverage map builder + test selector
│   │   ├── test_mapper.py         # AST static test mapping fallback
│   │   ├── test_runner.py         # Pytest execution wrapper
│   │   ├── traceability.py        # ISO 26262 requirements/ASIL traceability
│   │   ├── timing_service.py      # Test timing overrides from JSON
│   │   └── simple_mapper.py       # Lightweight static mapping
│   └── demo/
│       ├── setup_demo.py          # Demo repo builder
│       └── codebase/              # Automotive ECU test suite
│           ├── src/               # 6 source modules
│           ├── tests/             # 5 test files (26 test functions)
│           ├── conftest.py        # Bench fixture with per-level latency
│           ├── pytest.ini         # Marker registration
│           └── requirements.json   # 14 ISO 26262 requirements
├── .tia_cache/                    # Cached coverage maps (gitignored)
├── .demo_repo/                    # Built demo git repo (gitignored)
├── requirements.txt
└── .env                           # GitHub OAuth credentials (gitignored)

frontend/
├── src/
│   ├── main.jsx                   # React root
│   ├── App.jsx                    # Main app: state, API calls, layout
│   ├── App.css / index.css        # Styles (Tailwind)
│   ├── components/
│   │   ├── InputForm.jsx          # Repo URL + commit input
│   │   ├── Navbar.jsx             # Top navigation bar
│   │   ├── GithubAuthGuard.jsx    # Auth gate
│   │   ├── GithubCallback.jsx     # OAuth terminal screen
│   │   ├── ProfileMenu.jsx        # User dropdown
│   │   ├── EmptyState.jsx         # Initial state
│   │   ├── LoadingState.jsx       # Terminal-style loading
│   │   └── Dashboard/
│   │       ├── Header.jsx         # Commit summary
│   │       ├── KPIs.jsx           # Key metrics cards
│   │       ├── Charts.jsx         # Bar + donut charts
│   │       ├── RequirementsImpact.jsx  # ISO 26262 panel
│   │       ├── DependencyTrace.jsx     # File-to-test traceability
│   │       └── MapResults.jsx     # Quick Map results
│   └── assets/                    # Static images
├── public/
│   ├── favicon.svg
│   └── icons.svg
├── package.json
├── vite.config.js
└── index.html
```
