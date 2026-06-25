# API Reference

## Base URL

```
http://localhost:8000
```

Configured via `VITE_API_BASE` environment variable in the frontend (defaults to `http://localhost:8000`).

## Authentication

### POST `/api/auth/github`

Exchanges a temporary GitHub OAuth authorization code for an access token.

**Request:**
```json
{
  "code": "ghu_XXXXXXXXXXXXXXXXXXXX"
}
```

**Response (200):**
```json
{
  "access_token": "gho_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
}
```

**Error (400):**
```json
{
  "detail": "error description from GitHub"
}
```

**Flow:**
1. Frontend redirects to `https://github.com/login/oauth/authorize?client_id=...&redirect_uri=...&scope=repo`
2. GitHub redirects back to `/auth/callback?code=...`
3. Frontend sends the code to this endpoint
4. Backend proxies to `https://github.com/login/oauth/access_token`
5. Token is returned to the frontend, which stores it in `localStorage`

---

## Analysis Endpoints

### POST `/api/analyze`

Runs the full Smart-TIA pipeline against any Git repository.

**Request:**
```json
{
  "repo_url": "https://github.com/owner/repo",
  "target_commit": "a1b2c3d",
  "base_commit": "e5f6g7h",
  "target_dir": "src/",
  "tests_dir": "tests",
  "github_token": "gho_..."
}
```

**Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `repo_url` | string | Yes | — | Repository URL or local path |
| `target_commit` | string | No | `"HEAD"` | Commit hash, branch name, or tag |
| `base_commit` | string | No | Parent of target | Explicit base for diff (optional) |
| `target_dir` | string | No | `"src/"` | Source code directory |
| `tests_dir` | string | No | `"tests"` | Test files directory |
| `github_token` | string | No | null | GitHub OAuth token for private repos |

**Response (200):**

```json
{
  "pipeline_run": {
    "commit_hash": "a1b2c3d",
    "commit_message": "fix: correct SOC gain calculation",
    "base_commit": "e5f6g7h",
    "timestamp": "Just now",
    "status": "success"
  },
  "metrics": {
    "total_tests_in_suite": 26,
    "tests_executed": 3,
    "tests_skipped": 23,
    "standard_run_time_seconds": 5.2,
    "smart_run_time_seconds": 0.6,
    "time_saved_percentage": 88.5,
    "hil_tests_total": 11,
    "hil_tests_skipped": 8
  },
  "analysis": {
    "selection_method": "coverage",
    "confidence": "high",
    "fallback_reason": null,
    "modified_files": ["src/battery_management.py"],
    "impacted_functions": ["src/battery_management.py::compute_soc"],
    "selected_tests": [
      "tests/test_battery_management.py::test_soc_estimation",
      "tests/test_battery_management.py::test_soc_ranges"
    ],
    "all_selected_passed": true,
    "all_test_files": [
      "tests/test_battery_management.py",
      "tests/test_brake_system.py",
      "tests/test_can_bus.py",
      "tests/test_diagnostics.py",
      "tests/test_motor_controller.py"
    ]
  },
  "traceability": {
    "impacted_requirements": [
      {
        "id": "SR-BMS-001",
        "title": "Battery State of Charge Estimation",
        "asil": "C",
        "component": "BMS",
        "tests": [
          "tests/test_battery_management.py::test_soc_estimation",
          "tests/test_battery_management.py::test_soc_ranges"
        ]
      }
    ],
    "highest_asil": "C"
  },
  "dependency_trace": [
    {
      "modified_file": "src/battery_management.py",
      "impacted_tests": [
        {
          "test_name": "test_soc_estimation",
          "status": "passed",
          "duration_ms": 152,
          "level": "SIL",
          "asil": "C",
          "requirement": "SR-BMS-001"
        }
      ]
    }
  ]
}
```

**Error (400):**
```json
{
  "detail": "Analysis failed: <error message>"
}
```

---

### POST `/api/analyze/map`

Lightweight static mapping. Does NOT execute any tests — returns only the impact analysis.

**Request:**
```json
{
  "repo_url": "https://github.com/owner/repo",
  "target_commit": "a1b2c3d",
  "base_commit": "e5f6g7h",
  "source_dir": "src/",
  "tests_dir": "tests",
  "github_token": "gho_..."
}
```

**Response (200):**

```json
{
  "status": "success",
  "commit": {
    "hash": "a1b2c3d",
    "base": "e5f6g7h"
  },
  "diff_summary": {
    "modified_files": ["src/battery_management.py"],
    "impacted_functions": ["src/battery_management.py::compute_soc"],
    "total_changed": 1
  },
  "test_mapping": {
    "selected_test_files": ["tests/test_battery_management.py"],
    "by_source": {
      "src/battery_management.py": ["tests/test_battery_management.py"]
    },
    "total_impacted_test_files": 1
  },
  "all_test_files": [
    "tests/test_battery_management.py",
    "tests/test_brake_system.py",
    "tests/test_can_bus.py",
    "tests/test_diagnostics.py",
    "tests/test_motor_controller.py"
  ],
  "timing": {
    "standard_run_time_seconds": 5.2,
    "smart_run_time_seconds": 0.6,
    "time_saved_percentage": 88.5
  },
  "source_dir": "src/",
  "tests_dir": "tests"
}
```

---

### POST `/api/analyze/demo`

Runs a pre-built demo scenario on the bundled automotive ECU codebase.

**Request:**
```json
{
  "scenario": "safe"
}
```

**Valid scenarios:** `safe`, `regression`, `transitive`, `safety_net`

**Response (200):** Same as `/api/analyze` with an additional `scenario` field:

```json
{
  "scenario": {
    "key": "safe",
    "label": "Safe refactor: BMS docstring",
    "expectation": "Battery management tests are selected; all pass."
  },
  "pipeline_run": { ... },
  "metrics": { ... },
  "analysis": { ... },
  "traceability": { ... },
  "dependency_trace": [ ... ]
}
```

---

### GET `/api/analyze/demo/scenarios`

Lists available demo scenarios for rendering the demo buttons.

**Response (200):**
```json
{
  "safe": {
    "label": "Safe refactor: BMS docstring",
    "expectation": "Battery management tests are selected; all pass."
  },
  "regression": {
    "label": "Regression injection: BMS SOC gain",
    "expectation": "Battery management tests are selected; the SOC test fails."
  },
  "transitive": {
    "label": "Transitive dependency: sensor_utils clamp",
    "expectation": "Coverage-based selection catches an indirect change to a shared helper."
  },
  "safety_net": {
    "label": "Safety-net: untested function",
    "expectation": "Full suite runs as a safety fallback because a new, unmappable function is introduced."
  }
}
```

---

### GET/POST `/api/health`

Liveness check.

**Response (200):**
```json
{
  "status": "ok",
  "service": "SmartTIA Engine"
}
```

---

## Response Schema Reference

### `pipeline_run`

| Field | Type | Description |
|-------|------|-------------|
| `commit_hash` | string | Short (7-char) target commit hash |
| `commit_message` | string | First line of commit message |
| `base_commit` | string | Short (7-char) base commit hash |
| `timestamp` | string | Currently `"Just now"` |
| `status` | string | `"success"` if all selected tests passed, `"failed"` otherwise |

### `metrics`

| Field | Type | Description |
|-------|------|-------------|
| `total_tests_in_suite` | integer | Total tests in the test suite |
| `tests_executed` | integer | Tests selected + executed by SmartTIA |
| `tests_skipped` | integer | Tests skipped (`total - executed`) |
| `standard_run_time_seconds` | float | Estimated time to run full suite |
| `smart_run_time_seconds` | float | Estimated time to run selected tests |
| `time_saved_percentage` | float | `(1 - smart/standard) * 100` |
| `hil_tests_total` | integer | Total HIL-level tests in suite |
| `hil_tests_skipped` | integer | HIL tests skipped by SmartTIA |

### `analysis`

| Field | Type | Description |
|-------|------|-------------|
| `selection_method` | string | `"coverage"`, `"ast"`, or `"full-fallback"` |
| `confidence` | string | `"high"` or `"low"` |
| `fallback_reason` | string or null | Description of why fallback was triggered |
| `modified_files` | string[] | Source files changed in the diff |
| `impacted_functions` | string[] | Functions impacted (`"file::func"` format) |
| `selected_tests` | string[] | Selected test nodeids |
| `all_selected_passed` | boolean | Whether all selected tests passed |
| `all_test_files` | string[] | All test files in the repo |

### `traceability`

| Field | Type | Description |
|-------|------|-------------|
| `impacted_requirements` | array | List of requirements with tests, ASIL, component |
| `highest_asil` | string | Highest ASIL among impacted requirements |

### `dependency_trace`

Array of objects, each with:
| Field | Type | Description |
|-------|------|-------------|
| `modified_file` | string | Source file that was changed |
| `impacted_tests` | array | Test entries with name, status, duration, level, asil, requirement |
