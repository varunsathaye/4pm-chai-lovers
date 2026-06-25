# Demo System

## Overview

SmartTIA includes a self-contained automotive Electronic Control Unit (ECU) test suite that demonstrates all features of the engine. The demo is built from templates into a temporary Git repository with multiple scenario branches, enabling a repeatable, scripted demonstration of every selection tier.

## Demo Setup

The demo repo is built by `backend/app/demo/setup_demo.py`:

```bash
cd backend
python -m app.demo.setup_demo    # Build or reset the demo repo
uvicorn app.main:app --reload      # Start the API server
```

The builder:
1. Copies source and test templates from `app/demo/codebase/` into a fresh Git repo
2. Creates a baseline commit on `main`
3. Creates 4 scenario branches, each with a targeted code change
4. Records commit hashes to `.demo_repo/commits.json`

## Demo Codebase

### Source Modules (6 files)

| Module | File | Purpose |
|--------|------|---------|
| Battery Management | `src/battery_management.py` | SOC estimation, charge interlock, cell balancing, thermal state monitoring |
| Motor Controller | `src/motor_controller.py` | Torque limiting, RPM conversion, regenerative braking |
| Brake System | `src/brake_system.py` | ABS: slip ratio calculation, wheel-lock detection, pressure modulation |
| CAN Bus | `src/can_bus.py` | J1939-style signal encoding/decoding, CRC-8 frame checksum |
| Diagnostics | `src/diagnostics.py` | DTC validation, detection, severity classification |
| Sensor Utils | `src/sensor_utils.py` | Shared utilities: `clamp()`, moving average filter |

### Key Constants

| Module | Constants |
|--------|-----------|
| `battery_management.py` | `V_MIN=3.0`, `V_MAX=4.2`, `MIN_CHARGE_TEMP_C=0`, `MAX_CHARGE_TEMP_C=45`, `BALANCE_THRESHOLD_V=0.05` |
| `motor_controller.py` | `MAX_TORQUE_NM=320.0`, `MAX_RPM=16000`, `WHEEL_RADIUS_M=0.33`, `GEAR_RATIO=9.0` |
| `brake_system.py` | `SLIP_THRESHOLD=0.2`, `MAX_BRAKE_PRESSURE_BAR=180.0` |
| `diagnostics.py` | `DTC_SEVERITY` dictionary, `LOW_VOLTAGE_LIMIT=3.2` |

### Test Suite (26 test functions across 5 files)

| Test File | Tests | Level | Requirements | ASIL |
|-----------|-------|-------|-------------|------|
| `test_battery_management.py` | 6 | SIL | SR-BMS-001 to SR-BMS-004 | C, B |
| `test_motor_controller.py` | 6 | HIL | SR-MOT-001 to SR-MOT-003 | D, B, C |
| `test_brake_system.py` | 5 | HIL | SR-BRK-001, SR-BRK-002 | D |
| `test_can_bus.py` | 4 | UNIT | SR-CAN-001, SR-CAN-002 | B |
| `test_diagnostics.py` | 5 | UNIT | SR-DIAG-001, SR-DIAG-002 | B |

**Total: 26 test cases, 14 ISO 26262 requirements, ASIL ratings from B to D**

### Test Infrastructure

**`conftest.py`** — Simulated execution latency via an autouse `bench` fixture:
- UNIT tests: 50ms (cheap)
- SIL tests: 150ms (medium)
- HIL tests: 400ms (expensive — hardware-in-the-loop)

**`pytest.ini`** — Registers custom markers: `req`, `level`, `asil`

**`requirements.json`** — 14 ISO 26262 requirements:
```json
{
  "SR-BMS-001": {
    "title": "Battery State of Charge Estimation",
    "asil": "C",
    "component": "BMS"
  }
}
```

## Demo Scenarios

### 1. Safe Refactor (`scenario/safe`)

| Detail | Value |
|--------|-------|
| **File Changed** | `src/battery_management.py` |
| **Change** | Docstring comment added inside `compute_soc()` |
| **Expected Outcome** | 3 battery tests selected, all pass |
| **What it proves** | Minimal change → small test subset. No regressions. |

### 2. Regression Caught (`scenario/regression`)

| Detail | Value |
|--------|-------|
| **File Changed** | `src/battery_management.py` |
| **Change** | SOC gain formula changed from `* 100` to `* 10` (intentional bug) |
| **Expected Outcome** | 3 tests selected, SOC estimation test **FAILS** |
| **What it proves** | SmartTIA correctly selects the tests that expose the bug. The failed test's assertion catches the `0.1 → 1.0` SOC discrepancy instead of the expected `0.83 → 8.3`. |

### 3. Transitive Dependency (`scenario/transitive`)

| Detail | Value |
|--------|-------|
| **File Changed** | `src/sensor_utils.py` |
| **Change** | `clamp()` function lower bound dropped |
| **Expected Outcome** | Coverage re-selects battery tests (they executed `clamp()` at runtime), **FAILURE detected** |
| **What it proves** | **The headline feature.** `compute_soc()` in `battery_management.py` calls `clamp()` from `sensor_utils.py`. No test file imports or mentions `sensor_utils` textually. A text/AST matcher would select ZERO tests and miss the bug. Coverage-based selection finds the transitive dependency and catches the regression. |

### 4. Safety Net (`scenario/safety-net`)

| Detail | Value |
|--------|-------|
| **File Changed** | `src/battery_management.py` |
| **Change** | New untested function `pack_soc()` added |
| **Expected Outcome** | Full suite runs (safety fallback engaged), 26/26 tests executed |
| **What it proves** | When a change cannot be confidently mapped, SmartTIA falls back to the full suite. All 26 tests run, guaranteeing no defect is silently missed. |

## Scenario Comparison Matrix

| Scenario | Change Type | Tier Used | Tests Selected | Tests Skipped | Result |
|----------|------------|-----------|---------------|--------------|--------|
| Safe refactor | Comment addition | AST / Coverage | 3 | 23 | All pass |
| Regression | Formula bug | AST / Coverage | 3 | 23 | 1 fail (bug caught) |
| Transitive | Shared helper | **Coverage** | 3 | 23 | Failure detected |
| Safety net | Untested function | Full fallback | 26 | 0 | All pass (full suite) |

## API Endpoints for Demo

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/analyze/demo` | Run a scenario by key (`"safe"`, `"regression"`, `"transitive"`, `"safety_net"`) |
| `GET` | `/api/analyze/demo/scenarios` | List available scenarios with labels and expectations |

### Demo Response

The `/api/analyze/demo` endpoint returns the standard pipeline payload with an additional `scenario` field:

```json
{
  "scenario": {
    "key": "regression",
    "label": "Regression injection: BMS SOC gain",
    "expectation": "Battery management tests are selected; the SOC test fails."
  },
  "pipeline_run": { ... },
  "metrics": { ... },
  "analysis": { ... },
  "traceability": { ... },
  "dependency_trace": [ ... ]
}
```

## Demo-Day Reset

```bash
cd backend
python -m app.demo.setup_demo    # Clean rebuild
uvicorn app.main:app --reload
```

This deletes the old `.demo_repo/`, rebuilds from templates with fresh commit hashes, and regenerates `commits.json`.
