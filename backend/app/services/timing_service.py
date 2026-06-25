"""Read test-timing metadata from a JSON file inside the tests directory.

The file (expected name ``test_timings.json`` at the root of ``tests_dir``) maps
each test file path to a hardcoded duration in seconds, e.g.::

    {
      "tests/test_abs_brakes.cpp": 9.0,
      "tests/test_speed_sensor.cpp": 5.0,
      ...
    }

These values are used to compute ``standard_run_time_seconds``,
``smart_run_time_seconds`` and ``time_saved_percentage`` even when the TIA
pipeline skips actual test execution (e.g. for non-Python repos).
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Union

import git


def read_test_timings(
    repo_path: str,
    commit_sha: str,
    tests_dirs: Union[str, List[str]],
    filename: str = "test_execution_time.json",
) -> Dict[str, float]:
    """Read test timing JSON from the git tree at *commit_sha*.

    Checks each directory in *tests_dirs* for the timing file and merges
    all results. Returns ``{test_file_path: duration_seconds}`` or an empty
    dict when no timing file exists or cannot be parsed.
    """
    if isinstance(tests_dirs, str):
        tests_dirs = [tests_dirs]
    repo = git.Repo(repo_path)
    merged: Dict[str, float] = {}
    for td in tests_dirs:
        timing_path = os.path.join(td, filename).replace("\\", "/")
        try:
            blob = repo.commit(commit_sha).tree / timing_path
            content = blob.data_stream.read().decode("utf-8", errors="ignore")
            data = json.loads(content)
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, (int, float)):
                        merged[k] = float(v)
        except (KeyError, json.JSONDecodeError, TypeError, Exception):
            pass
    return merged


def compute_timing_metrics(
    timings: Dict[str, float],
    selected_nodeids: List[str],
    total_test_count: int,
) -> Dict[str, Any]:
    """Derive time-based KPIs from the timing map and selected test list.

    Returns::

        {
            "standard_run_time_seconds": float,
            "smart_run_time_seconds": float,
            "time_saved_percentage": float,
        }
    """
    if not timings:
        return {
            "standard_run_time_seconds": 0.0,
            "smart_run_time_seconds": 0.0,
            "time_saved_percentage": 0.0,
        }

    total_time = sum(timings.values())

    smart_time = 0.0
    seen: set[str] = set()
    for nodeid in selected_nodeids:
        file_part = nodeid.split("::")[0]
        if file_part in seen:
            continue
        seen.add(file_part)
        smart_time += timings.get(file_part, 0.0)

    time_saved = max(total_time - smart_time, 0.0)
    time_saved_pct = round((time_saved / total_time) * 100, 1) if total_time > 0 else 0.0

    return {
        "standard_run_time_seconds": round(total_time, 1),
        "smart_run_time_seconds": round(smart_time, 1),
        "time_saved_percentage": time_saved_pct,
    }
