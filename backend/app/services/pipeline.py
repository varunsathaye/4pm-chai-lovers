"""End-to-end Smart-TIA pipeline.

clone -> diff (AST) -> map tests (AST) -> run only impacted tests + full
baseline -> assemble the dashboard payload with 100% real metrics.
"""
from __future__ import annotations

import shutil
import tempfile
from typing import Any, Dict, List, Optional

import git

from app.services import diff_analyzer, test_mapper, test_runner


def _short(sha: str) -> str:
    return sha[:7] if sha else sha


def _resolve_base(repo: git.Repo, target_commit: str, base_commit: Optional[str]) -> str:
    """Default the base to the target's first parent when not supplied."""
    if base_commit:
        return base_commit
    commit = repo.commit(target_commit)
    if commit.parents:
        return commit.parents[0].hexsha
    return commit.hexsha  # root commit: diff against itself -> treated as all-new


def run_analysis(
    repo_source: str,
    target_commit: str = "HEAD",
    base_commit: Optional[str] = None,
    target_dir: str = "src/",
    tests_dir: str = "tests",
) -> Dict[str, Any]:
    """Run the full pipeline. ``repo_source`` may be a local path or a clone URL.

    Returns the dashboard payload (pipeline_run / metrics / dependency_trace /
    analysis) and never raises on a normal "no tests matched" outcome.
    """
    work_dir = tempfile.mkdtemp(prefix="smarttia_")
    repo = git.Repo.clone_from(repo_source, work_dir)
    try:
        resolved_base = _resolve_base(repo, target_commit, base_commit)
        target_sha = repo.commit(target_commit).hexsha
        commit_obj = repo.commit(target_sha)

        # 1. Diff -> impacted source functions (AST for .py)
        diff_data = diff_analyzer.get_impacted_files(
            work_dir, resolved_base, target_sha, target_dir=target_dir
        )

        # 2. Map impacted source -> impacted tests (AST for .py)
        mapping = test_mapper.map_tests(
            diff_data, work_dir, target_sha, tests_dir_prefix=tests_dir
        )
        selected_files = mapping["selected_test_files"]

        # 3. Check out the target revision so tests run against the new code
        repo.git.checkout(target_sha, force=True)

        # 4. Execute: full baseline + impacted subset (real timings)
        full = test_runner.run_full_suite(work_dir, tests_dir)
        smart = test_runner.run_selected(work_dir, selected_files)

        return _build_payload(
            commit_obj=commit_obj,
            base_sha=resolved_base,
            diff_data=diff_data,
            mapping=mapping,
            full=full,
            smart=smart,
        )
    finally:
        # GitPython holds OS handles on Windows; release them before cleanup.
        repo.close()
        shutil.rmtree(work_dir, ignore_errors=True)


def _build_payload(commit_obj, base_sha, diff_data, mapping, full, smart) -> Dict[str, Any]:
    total = full["total_tests"]
    executed = smart["total_tests"]
    skipped = max(total - executed, 0)

    std_time = full["duration_seconds"]
    smart_time = smart["duration_seconds"]
    time_saved = round((1 - (smart_time / std_time)) * 100, 1) if std_time > 0 else 0.0

    all_passed = smart.get("passed", True)
    status = "success" if all_passed else "failed"

    # dependency_trace: group the executed tests under each modified source file
    smart_by_file: Dict[str, List[dict]] = {}
    for t in smart["tests"]:
        smart_by_file.setdefault(t["file"], []).append({
            "test_name": t["test_name"],
            "status": t["status"],
            "duration_ms": t["duration_ms"],
        })

    dependency_trace = []
    for source_file, test_files in mapping["by_source"].items():
        impacted_tests: List[dict] = []
        for tf in test_files:
            impacted_tests.extend(smart_by_file.get(tf, []))
        if impacted_tests:
            dependency_trace.append({
                "modified_file": source_file,
                "impacted_tests": impacted_tests,
            })

    impacted_functions: List[str] = []
    for item in diff_data.get("added_or_modified", []):
        impacted_functions.extend(item.get("impacted_functions", []))

    return {
        "pipeline_run": {
            "commit_hash": _short(commit_obj.hexsha),
            "commit_message": commit_obj.message.strip().split("\n")[0],
            "base_commit": _short(base_sha),
            "timestamp": "Just now",
            "status": status,
        },
        "metrics": {
            "total_tests_in_suite": total,
            "tests_executed": executed,
            "tests_skipped": skipped,
            "standard_run_time_seconds": std_time,
            "smart_run_time_seconds": smart_time,
            "time_saved_percentage": time_saved,
        },
        "analysis": {
            "modified_files": [i["file"] for i in diff_data.get("added_or_modified", [])],
            "impacted_functions": sorted(set(impacted_functions)),
            "selected_test_files": mapping["selected_test_files"],
            "all_selected_passed": all_passed,
        },
        "dependency_trace": dependency_trace,
    }
