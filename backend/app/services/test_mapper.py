"""Map impacted source code to the test files that exercise it.

For Python test files we parse the AST and extract:
  * the modules they import      (``from src.battery_management import ...``)
  * every identifier they reference (function/attribute names)

A test is mapped to an impacted source file when it imports that module *or*
references one of the specific functions the diff flagged as changed. Parsing
the AST (instead of plain substring search) means a function name buried in a
comment or unrelated string never produces a false mapping.

For non-Python repositories we fall back to a whole-word keyword scan.
"""
from __future__ import annotations

import ast
import os
import re
from typing import Any, Dict, List, Set

import git


def _module_basename(file_path: str) -> str:
    return os.path.splitext(os.path.basename(file_path))[0]


def _impacted_index(impacted_items: List[dict]) -> Dict[str, Dict[str, Any]]:
    """Build {source_file: {module, functions}} for quick matching."""
    index: Dict[str, Dict[str, Any]] = {}
    for item in impacted_items:
        path = item.get("file", "")
        index[path] = {
            "module": _module_basename(path),
            "functions": set(item.get("impacted_functions", [])),
        }
    return index


def _python_test_symbols(source: str) -> tuple[Set[str], Set[str]]:
    """Return (imported_module_basenames, referenced_identifiers)."""
    imported: Set[str] = set()
    referenced: Set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return imported, referenced

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[-1])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module.split(".")[-1])
            for alias in node.names:
                referenced.add(alias.name)
        elif isinstance(node, ast.Name):
            referenced.add(node.id)
        elif isinstance(node, ast.Attribute):
            referenced.add(node.attr)
    return imported, referenced


def map_tests(
    diff_data: Dict[str, Any],
    repo_path: str,
    target_commit: str,
    tests_dir_prefix: str = "tests",
) -> Dict[str, Any]:
    """Return mapping of impacted source files -> impacted test files.

    Shape::

        {
          "selected_test_files": ["tests/test_battery_management.py", ...],
          "by_source": {"src/battery_management.py": ["tests/test_..."], ...},
        }
    """
    impacted_items = diff_data.get("added_or_modified", [])
    index = _impacted_index(impacted_items)

    by_source: Dict[str, List[str]] = {item["file"]: [] for item in impacted_items}
    selected: Set[str] = set()

    if not impacted_items:
        return {"selected_test_files": [], "by_source": by_source}

    repo = git.Repo(repo_path)
    commit = repo.commit(target_commit)

    for blob in commit.tree.traverse():
        if blob.type != "blob":
            continue
        path = blob.path
        if not (path.startswith(tests_dir_prefix) and path.endswith(".py")):
            continue

        content = blob.data_stream.read().decode("utf-8", errors="ignore")
        imported, referenced = _python_test_symbols(content)

        for source_file, meta in index.items():
            module = meta["module"]
            funcs = meta["functions"]
            hit = (module in imported) or bool(funcs & referenced)
            if not hit and not funcs:
                # Module changed but no specific functions resolved: fall back
                # to a whole-word keyword scan so we never under-select.
                if re.search(r"\b" + re.escape(module) + r"\b", content):
                    hit = True
            if hit:
                by_source[source_file].append(path)
                selected.add(path)

    return {
        "selected_test_files": sorted(selected),
        "by_source": {k: sorted(v) for k, v in by_source.items()},
    }
