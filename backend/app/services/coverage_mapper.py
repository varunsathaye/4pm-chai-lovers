"""Coverage-based test impact mapping (the precision engine).

This is the gold-standard approach used by real-world TIA systems. Instead of
guessing which tests relate to a change from imports/text, we *observe* it:

  1. Once, on the known-good baseline commit, run the whole suite with
     per-test coverage contexts (``pytest --cov --cov-context=test``).
  2. From the coverage database, build a map:
         (source_file, function) -> { tests that executed it }
     Mapping covered line numbers to their enclosing function via the AST.
  3. When a commit changes some functions, select every test whose coverage
     touched those functions.

Because coverage records what actually executed at runtime, this catches
**transitive / indirect** dependencies: if a test calls A which internally
calls a changed helper B, the test is correctly selected -- even though the
test never mentions B. Text/AST matching cannot see that.

The map is cached on disk per baseline commit so repeated analyses are fast.
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


def _function_ranges(source: str) -> List[Tuple[str, int, int]]:
    """Return (function_name, start_line, end_line) for each def/method."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    ranges: List[Tuple[str, int, int]] = []

    class _V(ast.NodeVisitor):
        def _scope(self, node):
            end = getattr(node, "end_lineno", node.lineno)
            ranges.append((node.name, node.lineno, end))
            self.generic_visit(node)

        visit_FunctionDef = _scope
        visit_AsyncFunctionDef = _scope

    _V().visit(tree)
    return ranges


def _enclosing_function(ranges: List[Tuple[str, int, int]], line: int) -> str | None:
    """Smallest function range that contains ``line``."""
    best = None
    for name, start, end in ranges:
        if start <= line <= end:
            span = end - start
            if best is None or span < best[0]:
                best = (span, name)
    return best[1] if best else None


def _clean_context(ctx: str) -> str:
    """pytest-cov contexts look like 'tests/x.py::test_y|run' -> nodeid."""
    if not ctx:
        return ""
    return ctx.split("|", 1)[0]


def build_coverage_map(repo_dir: str, source_dir: str = "src", tests_dir: str = "tests") -> Dict[str, Any]:
    """Run the suite with coverage contexts and build the function->tests map.

    Must be called with ``repo_dir`` already checked out at the baseline commit.
    Returns a JSON-serialisable dict::

        {
          "by_function": { "src/file.py::func": ["tests/..::test", ...] },
          "covered_files": ["src/file.py", ...],
          "ok": True
        }
    """
    data_file = os.path.join(repo_dir, ".coverage")
    if os.path.exists(data_file):
        os.remove(data_file)

    cmd = [
        sys.executable, "-m", "pytest", tests_dir,
        f"--cov={source_dir}", "--cov-context=test", "--cov-report=",
        "-q", "-p", "no:cacheprovider",
    ]
    proc = subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True, timeout=600)

    try:
        import coverage  # imported here so a missing plugin degrades gracefully
    except ImportError:
        return {"by_function": {}, "covered_files": [], "ok": False,
                "error": "coverage package not installed"}

    if not os.path.exists(data_file):
        return {"by_function": {}, "covered_files": [], "ok": False,
                "error": f"no coverage data produced: {proc.stdout[-400:]}"}

    cov = coverage.Coverage(data_file=data_file)
    cov.load()
    cdata = cov.get_data()

    repo_path = Path(repo_dir).resolve()
    by_function: Dict[str, Set[str]] = {}
    covered_files: Set[str] = set()
    ranges_cache: Dict[str, List[Tuple[str, int, int]]] = {}

    for measured in cdata.measured_files():
        abs_path = Path(measured).resolve()
        try:
            rel = abs_path.relative_to(repo_path).as_posix()
        except ValueError:
            continue
        if not rel.startswith(source_dir):
            continue
        covered_files.add(rel)

        if rel not in ranges_cache:
            try:
                ranges_cache[rel] = _function_ranges(abs_path.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                ranges_cache[rel] = []
        ranges = ranges_cache[rel]

        contexts_by_line = cdata.contexts_by_lineno(measured)
        for lineno, contexts in contexts_by_line.items():
            func = _enclosing_function(ranges, lineno)
            if not func:
                continue
            key = f"{rel}::{func}"
            bucket = by_function.setdefault(key, set())
            for ctx in contexts:
                nodeid = _clean_context(ctx)
                if nodeid and "::" in nodeid:
                    bucket.add(nodeid)

    has_data = bool(by_function) or bool(covered_files)
    return {
        "by_function": {k: sorted(v) for k, v in by_function.items()},
        "covered_files": sorted(covered_files),
        "ok": has_data,
    }


def select_tests(coverage_map: Dict[str, Any], diff_data: Dict[str, Any]) -> Dict[str, Any]:
    """Select tests impacted by a diff, using the coverage map.

    Returns selected test nodeids, a per-source-file breakdown, and any changed
    functions that could NOT be resolved against the map (these drive the
    safety fallback in the pipeline).
    """
    by_function: Dict[str, List[str]] = coverage_map.get("by_function", {})

    selected: Set[str] = set()
    by_source: Dict[str, List[str]] = {}
    unmapped: List[str] = []

    for item in diff_data.get("added_or_modified", []):
        source_file = item["file"]
        funcs = item.get("impacted_functions", [])
        file_tests: Set[str] = set()

        if not source_file.endswith(".py"):
            unmapped.append(source_file)
            continue

        if not funcs:
            # File changed but no enclosing function resolved (module-level
            # edit). Select every test that touched this file at all.
            hit_any = False
            for key, tests in by_function.items():
                if key.startswith(source_file + "::"):
                    file_tests.update(tests)
                    hit_any = True
            if not hit_any:
                unmapped.append(source_file)

        for func in funcs:
            key = f"{source_file}::{func}"
            if key in by_function:
                file_tests.update(by_function[key])
            else:
                unmapped.append(key)

        if file_tests:
            by_source[source_file] = sorted(file_tests)
            selected.update(file_tests)

    return {
        "selected_nodeids": sorted(selected),
        "by_source": by_source,
        "unmapped": unmapped,
    }
