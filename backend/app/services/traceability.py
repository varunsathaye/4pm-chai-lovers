"""Requirements traceability (ISO 26262 / ASIL) for the impacted tests.

Automotive testing is requirement-driven: every test traces to a software
requirement, which carries a safety classification (ASIL A-D). This module
statically reads the ``@pytest.mark.req(...) / .level(...) / .asil(...)``
markers from the test files and joins them with the repo's
``requirements.json`` registry, so the dashboard can show:

    code change -> impacted requirement(s) -> tests -> ASIL rating

That mapping is exactly what a safety-critical V-model QA process cares about,
and almost no generic TIA tool surfaces it.
"""
from __future__ import annotations

import ast
import json
import os
from typing import Any, Dict, List, Union

import git

_MARKERS = {"req", "level", "asil"}


def _marker_args(decorator: ast.expr) -> tuple[str | None, list[str]]:
    """If a decorator is ``pytest.mark.<name>(...)``, return (name, str_args)."""
    if not isinstance(decorator, ast.Call):
        return None, []
    func = decorator.func
    # match attribute chain ending in `.mark.<name>`
    if isinstance(func, ast.Attribute) and func.attr in _MARKERS:
        parent = func.value
        if isinstance(parent, ast.Attribute) and parent.attr == "mark":
            args = [a.value for a in decorator.args if isinstance(a, ast.Constant)]
            return func.attr, [str(a) for a in args]
    return None, []


def _module_level_markers(tree: ast.Module) -> Dict[str, str]:
    """Read ``pytestmark = pytest.mark.level('SIL')`` style module markers."""
    result: Dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "pytestmark" for t in node.targets
        ):
            calls = node.value.elts if isinstance(node.value, (ast.List, ast.Tuple)) else [node.value]
            for call in calls:
                name, args = _marker_args(call)
                if name and args:
                    result[name] = args[0]
    return result


def extract_test_markers(repo_path: str, target_commit: str, tests_dirs: Union[str, List[str]] = "tests") -> Dict[str, Dict[str, str]]:
    """Return ``{ test_nodeid: {req, level, asil} }`` read from the AST."""
    if isinstance(tests_dirs, str):
        tests_dirs = [tests_dirs]
    repo = git.Repo(repo_path)
    commit = repo.commit(target_commit)
    result: Dict[str, Dict[str, str]] = {}

    for blob in commit.tree.traverse():
        if blob.type != "blob":
            continue
        path = blob.path
        if not (any(path.startswith(d) for d in tests_dirs) and path.endswith(".py")):
            continue
        source = blob.data_stream.read().decode("utf-8", errors="ignore")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        module_markers = _module_level_markers(tree)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                info = dict(module_markers)
                for dec in node.decorator_list:
                    name, args = _marker_args(dec)
                    if name and args:
                        info[name] = args[0]
                nodeid = f"{path}::{node.name}"
                result[nodeid] = info
    return result


def load_requirements_registry(repo_path: str, target_commit: str) -> Dict[str, Any]:
    """Load ``requirements.json`` from the repo root (if present)."""
    repo = git.Repo(repo_path)
    commit = repo.commit(target_commit)
    try:
        blob = commit.tree / "requirements.json"
    except KeyError:
        return {}
    try:
        return json.loads(blob.data_stream.read().decode("utf-8", errors="ignore"))
    except json.JSONDecodeError:
        return {}


def build_traceability(markers: Dict[str, Dict[str, str]], registry: Dict[str, Any],
                       selected_nodeids: List[str]) -> Dict[str, Any]:
    """Aggregate impacted requirements for the selected tests."""
    requirements: Dict[str, Dict[str, Any]] = {}
    for nodeid in selected_nodeids:
        info = markers.get(nodeid, {})
        req_id = info.get("req")
        if not req_id:
            continue
        meta = registry.get(req_id, {})
        entry = requirements.setdefault(req_id, {
            "id": req_id,
            "title": meta.get("title", "(untracked requirement)"),
            "asil": meta.get("asil") or info.get("asil", "QM"),
            "component": meta.get("component", ""),
            "tests": [],
        })
        entry["tests"].append(nodeid)

    impacted = sorted(requirements.values(), key=lambda r: r["id"])
    return {
        "impacted_requirements": impacted,
        "highest_asil": _highest_asil(impacted),
    }


_ASIL_ORDER = {"QM": 0, "A": 1, "B": 2, "C": 3, "D": 4}


def _highest_asil(requirements: List[Dict[str, Any]]) -> str:
    best = "QM"
    for r in requirements:
        if _ASIL_ORDER.get(r.get("asil", "QM"), 0) > _ASIL_ORDER.get(best, 0):
            best = r["asil"]
    return best
