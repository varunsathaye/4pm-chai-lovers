"""Run pytest and capture real execution metrics.

Uses the ``pytest-json-report`` plugin to get structured, per-test results
(outcome + phase durations) plus the total session duration. Every number the
dashboard shows comes from here -- nothing is hard-coded.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional


def _run_pytest(repo_dir: str, test_targets: Optional[List[str]]) -> Dict[str, Any]:
    """Invoke pytest in ``repo_dir`` and return the parsed JSON report.

    ``test_targets`` is a list of test files/nodeids to run, or None to run the
    whole suite (full-regression baseline).
    """
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        report_path = tmp.name

    cmd = [
        sys.executable, "-m", "pytest",
        "--json-report",
        f"--json-report-file={report_path}",
        "-q", "-p", "no:cacheprovider",
    ]
    if test_targets is not None:
        cmd.extend(test_targets)

    proc = subprocess.run(
        cmd, cwd=repo_dir, capture_output=True, text=True, timeout=300
    )

    report: Dict[str, Any] = {}
    rp = Path(report_path)
    if rp.exists():
        try:
            report = json.loads(rp.read_text(encoding="utf-8"))
        finally:
            rp.unlink(missing_ok=True)

    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "report": report,
    }


def _test_duration_ms(test: Dict[str, Any]) -> int:
    """Total wall time of a test across setup/call/teardown phases."""
    total = 0.0
    for phase in ("setup", "call", "teardown"):
        total += float(test.get(phase, {}).get("duration", 0.0) or 0.0)
    return int(round(total * 1000))


def _parse_tests(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    parsed: List[Dict[str, Any]] = []
    for test in report.get("tests", []):
        nodeid = test.get("nodeid", "")
        file_part, _, name_part = nodeid.partition("::")
        parsed.append({
            "nodeid": nodeid,
            "file": file_part,
            "test_name": name_part or nodeid,
            "status": test.get("outcome", "unknown"),
            "duration_ms": _test_duration_ms(test),
        })
    return parsed


def run_full_suite(repo_dir: str, tests_dir: str) -> Dict[str, Any]:
    """Baseline: run the entire suite to measure standard-CI cost."""
    result = _run_pytest(repo_dir, [tests_dir])
    report = result["report"]
    tests = _parse_tests(report)
    return {
        "total_tests": report.get("summary", {}).get("total", len(tests)),
        "duration_seconds": round(float(report.get("duration", 0.0)), 2),
        "tests": tests,
    }


def run_selected(repo_dir: str, test_targets: List[str]) -> Dict[str, Any]:
    """Smart run: execute only the impacted tests.

    ``test_targets`` may be whole files (``tests/x.py``) or individual test
    node-ids (``tests/x.py::test_y``) -- pytest accepts both, so coverage-based
    selection gets per-test-case granularity for free.
    """
    if not test_targets:
        return {"total_tests": 0, "duration_seconds": 0.0, "tests": [], "passed": True}

    result = _run_pytest(repo_dir, test_targets)
    report = result["report"]
    tests = _parse_tests(report)
    passed = all(t["status"] == "passed" for t in tests) and result["returncode"] == 0
    return {
        "total_tests": report.get("summary", {}).get("total", len(tests)),
        "duration_seconds": round(float(report.get("duration", 0.0)), 2),
        "tests": tests,
        "passed": passed,
    }
