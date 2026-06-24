"""End-to-end Smart-TIA pipeline (coverage-precision engine).

Flow:
  clone -> build/load coverage map @ baseline -> diff (AST) -> select tests via
  coverage map -> safety fallback if low-confidence -> run only impacted tests +
  full baseline -> attach requirements traceability -> dashboard payload.

Selection strategy (in priority order):
  1. COVERAGE  - tests whose runtime coverage touched a changed function.
                 Catches transitive/indirect dependencies; per-test granularity.
  2. AST       - fallback when no coverage map could be built (e.g. an external
                 repo we can't safely instrument). Direct import/symbol match.
  3. FULL      - safety fallback: run everything when confidence is low
                 (unmapped change, config file, or zero tests selected).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import git

from app.services import coverage_mapper, diff_analyzer, test_mapper, test_runner, traceability

# Cache coverage maps per (repo, baseline commit) so repeated demos are fast.
CACHE_DIR = Path(__file__).resolve().parents[2] / ".tia_cache"


def _short(sha: str) -> str:
    return sha[:7] if sha else sha


def _resolve_base(repo: git.Repo, target_commit: str, base_commit: Optional[str]) -> str:
    if base_commit:
        return base_commit
    commit = repo.commit(target_commit)
    return commit.parents[0].hexsha if commit.parents else commit.hexsha


def _cache_key(repo_source: str, base_sha: str) -> Path:
    digest = hashlib.sha1(f"{repo_source}@{base_sha}".encode()).hexdigest()[:16]
    return CACHE_DIR / f"covmap_{digest}.json"


def _get_coverage_map(repo_source: str, work_dir: str, base_sha: str,
                      source_dir: str, tests_dir: str) -> Dict[str, Any]:
    """Load the cached coverage map for this baseline, or build + cache it."""
    cache_file = _cache_key(repo_source, base_sha)
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    cov_map = coverage_mapper.build_coverage_map(work_dir, source_dir.rstrip("/"), tests_dir)
    if cov_map.get("ok"):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(cov_map), encoding="utf-8")
    return cov_map


def run_analysis(
    repo_source: str,
    target_commit: str = "HEAD",
    base_commit: Optional[str] = None,
    target_dir: str = "src/",
    tests_dir: str = "tests",
) -> Dict[str, Any]:
    work_dir = tempfile.mkdtemp(prefix="smarttia_")
    repo = git.Repo.clone_from(repo_source, work_dir)
    try:
        resolved_base = _resolve_base(repo, target_commit, base_commit)
        target_sha = repo.commit(target_commit).hexsha
        commit_obj = repo.commit(target_sha)
        source_dir = target_dir.rstrip("/") or "src"

        # 1. Diff base..target -> impacted source functions (AST)
        diff_data = diff_analyzer.get_impacted_files(
            work_dir, resolved_base, target_sha, target_dir=target_dir
        )

        # 2. Build/load coverage map at the BASELINE (precision engine)
        repo.git.checkout(resolved_base, force=True)
        cov_map = _get_coverage_map(repo_source, work_dir, resolved_base, source_dir, tests_dir)

        # 3. Select impacted tests
        selection = _select(cov_map, diff_data, work_dir, target_sha, tests_dir)

        # 4. Traceability (requirements / ASIL) from the target revision
        markers = traceability.extract_test_markers(work_dir, target_sha, tests_dir)
        registry = traceability.load_requirements_registry(work_dir, target_sha)

        # 5. Execute against the TARGET revision (real pass/fail + timing)
        repo.git.checkout(target_sha, force=True)
        full = test_runner.run_full_suite(work_dir, tests_dir)
        smart = test_runner.run_selected(work_dir, selection["targets"])

        trace_block = traceability.build_traceability(
            markers, registry, [t["nodeid"] for t in smart["tests"]]
        )

        return _build_payload(
            commit_obj=commit_obj,
            base_sha=resolved_base,
            diff_data=diff_data,
            selection=selection,
            full=full,
            smart=smart,
            markers=markers,
            trace_block=trace_block,
        )
    finally:
        repo.close()
        shutil.rmtree(work_dir, ignore_errors=True)


def _select(cov_map, diff_data, work_dir, target_sha, tests_dir) -> Dict[str, Any]:
    """Pick tests with the best available strategy + decide on safety fallback."""
    changed_files = [i["file"] for i in diff_data.get("added_or_modified", [])]

    if cov_map.get("ok"):
        result = coverage_mapper.select_tests(cov_map, diff_data)
        method = "coverage"
        by_source = result["by_source"]
        targets = result["selected_nodeids"]
        unmapped = result["unmapped"]
    else:
        # No coverage map -> static AST mapping fallback
        ast_map = test_mapper.map_tests(diff_data, work_dir, target_sha, tests_dir_prefix=tests_dir)
        method = "ast"
        by_source = ast_map["by_source"]
        targets = ast_map["selected_test_files"]
        unmapped = [f for f in changed_files if not by_source.get(f)]

    # Safety fallback: low confidence -> run everything so we never miss a defect.
    fallback_reason = None
    if not targets:
        fallback_reason = "No impacted tests could be confidently identified."
    elif unmapped:
        fallback_reason = f"{len(unmapped)} changed item(s) could not be mapped to a test."

    if fallback_reason:
        return {
            "method": "full-fallback",
            "targets": [tests_dir],          # run the whole suite
            "by_source": by_source,
            "unmapped": unmapped,
            "confidence": "low",
            "fallback_reason": fallback_reason,
        }

    return {
        "method": method,
        "targets": targets,
        "by_source": by_source,
        "unmapped": unmapped,
        "confidence": "high",
        "fallback_reason": None,
    }


def _build_payload(commit_obj, base_sha, diff_data, selection, full, smart,
                   markers, trace_block) -> Dict[str, Any]:
    total = full["total_tests"]
    executed = smart["total_tests"]
    skipped = max(total - executed, 0)

    std_time = full["duration_seconds"]
    smart_time = smart["duration_seconds"]
    time_saved = round((1 - (smart_time / std_time)) * 100, 1) if std_time > 0 else 0.0

    all_passed = smart.get("passed", True)
    status = "success" if all_passed else "failed"

    # Annotate each executed test with its level/req/asil from the markers.
    def annotate(t: Dict[str, Any]) -> Dict[str, Any]:
        info = markers.get(t["nodeid"], {})
        return {
            "test_name": t["test_name"],
            "status": t["status"],
            "duration_ms": t["duration_ms"],
            "level": info.get("level", "UNIT"),
            "asil": info.get("asil", "QM"),
            "requirement": info.get("req", ""),
        }

    smart_by_file: Dict[str, List[dict]] = {}
    for t in smart["tests"]:
        smart_by_file.setdefault(t["file"], []).append(annotate(t))

    # dependency_trace: group executed tests under each modified source file.
    dependency_trace = []
    for source_file, test_targets in selection["by_source"].items():
        files = {tt.split("::")[0] for tt in test_targets}
        impacted_tests: List[dict] = []
        for f in sorted(files):
            impacted_tests.extend(smart_by_file.get(f, []))
        if impacted_tests:
            dependency_trace.append({
                "modified_file": source_file,
                "impacted_tests": impacted_tests,
            })

    # If we fell back to a full run, just show every executed test grouped by file.
    if not dependency_trace and smart_by_file:
        for f, tests in smart_by_file.items():
            dependency_trace.append({"modified_file": f, "impacted_tests": tests})

    impacted_functions: List[str] = []
    for item in diff_data.get("added_or_modified", []):
        for fn in item.get("impacted_functions", []):
            impacted_functions.append(f"{item['file']}::{fn}")

    # HIL tests skipped (the expensive ones) -- a strong automotive metric.
    all_levels = [markers.get(t["nodeid"], {}).get("level", "UNIT") for t in full["tests"]]
    executed_levels = [t["level"] for tests in smart_by_file.values() for t in tests]
    hil_total = all_levels.count("HIL")
    hil_executed = executed_levels.count("HIL")

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
            "hil_tests_total": hil_total,
            "hil_tests_skipped": max(hil_total - hil_executed, 0),
        },
        "analysis": {
            "selection_method": selection["method"],
            "confidence": selection["confidence"],
            "fallback_reason": selection["fallback_reason"],
            "modified_files": [i["file"] for i in diff_data.get("added_or_modified", [])],
            "impacted_functions": sorted(set(impacted_functions)),
            "selected_tests": [t["nodeid"] for t in smart["tests"]],
            "all_selected_passed": all_passed,
        },
        "traceability": trace_block,
        "dependency_trace": dependency_trace,
    }
