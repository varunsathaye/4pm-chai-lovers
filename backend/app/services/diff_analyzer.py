"""Diff analysis: turn a Git range (base..target) into the set of source
functions impacted by the change.

For Python files we parse the real Abstract Syntax Tree of the *target*
revision and map each changed line to its innermost enclosing function or
method. For other languages we fall back to a lightweight regex scan so the
engine still produces a useful answer on arbitrary repositories.

Cross-file call-chain analysis
-------------------------------
After identifying directly changed functions the module scans every source
file under *target_dir* looking for call sites (*i.e.* ``fun_name(``) that
reference a changed function.  Those calling files are added as "indirect"
entries (``change_type: "I"``) so the test mapper also selects tests for
the downstream callers.
"""
from __future__ import annotations

import ast
import os
import re
from typing import Any, Dict, List, Optional, Set

import git

# Non-function keywords that must never be reported as a "changed function"
# in the regex fallback path.
# NOTE: Only logical / control-flow keywords go here -- primitive type
# names (int, float, void, ...) are deliberately excluded because they
# legitimately appear as the first word of a function definition line
# (e.g. "float compute_soc(...)").
IGNORE_KEYWORDS = {
    "if", "for", "while", "switch", "catch", "else", "return",
    "public:", "private:", "protected:", "class", "struct", "namespace",
    "ESP_LOG", "Serial", "printf", "cout", "cin", "print",
    # C++ / common-language non-type keywords
    "template", "typename", "constexpr", "const_cast",
    "static_cast", "dynamic_cast", "reinterpret_cast", "sizeof",
    "typeid", "decltype", "throw", "new", "delete",
    "using", "typedef", "extern", "mutable",
    "explicit", "export", "friend",
    "nullptr", "true", "false", "this", "operator",
    # Python / script keywords that never start a function def
    "def", "import", "from", "async", "await", "lambda",
    "yield", "raise", "except", "finally", "with", "assert",
    "del", "pass", "break", "continue", "try",
}


def _changed_new_lines(raw_diff: str) -> List[int]:
    """Return the 1-based line numbers (new-file side) added/changed in a diff."""
    changed: List[int] = []
    new_line = 0
    for line in raw_diff.split("\n"):
        if line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            new_line = int(m.group(1)) if m else 0
        elif line.startswith("+") and not line.startswith("+++"):
            changed.append(new_line)
            new_line += 1
        elif line.startswith("-") and not line.startswith("---"):
            # deletion: associate with the current new-side position
            changed.append(max(1, new_line))
        elif not line.startswith("\\"):
            new_line += 1
    return changed


class _FuncRanges(ast.NodeVisitor):
    """Collect (qualified_name, start_line, end_line) for every def/class."""

    def __init__(self) -> None:
        self.ranges: List[tuple] = []
        self._stack: List[str] = []

    def _visit_scope(self, node) -> None:
        self._stack.append(node.name)
        qualified = ".".join(self._stack)
        end = getattr(node, "end_lineno", node.lineno)
        self.ranges.append((qualified, node.name, node.lineno, end))
        self.generic_visit(node)
        self._stack.pop()

    visit_FunctionDef = _visit_scope
    visit_AsyncFunctionDef = _visit_scope
    visit_ClassDef = _visit_scope


def _python_impacted_functions(source: str, changed_lines: List[int]) -> List[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    collector = _FuncRanges()
    collector.visit(tree)

    impacted: set[str] = set()
    for line in changed_lines:
        # innermost enclosing scope = smallest range that contains the line
        best = None
        for qualified, name, start, end in collector.ranges:
            if start <= line <= end:
                span = end - start
                if best is None or span < best[0]:
                    best = (span, name)
        if best:
            impacted.add(best[1])
    return sorted(impacted)


def _regex_impacted_functions(file_lines: List[str], changed_lines: List[int]) -> List[str]:
    impacted: set[str] = set()
    # Matches C/C++/Java/JS/etc function signatures:
    #   func_name(params)
    #   func_name(params) override { ... }
    #   func_name(params) const noexcept(true) { ... }
    #   ReturnType ClassName::func_name(params) { ... }
    #   def func_name(params):        (Python)
    # The named group captures only the plain function name.
    sig_re = re.compile(
        r"\b([a-zA-Z_]\w*)\s*"
        r"\([^)]*\)\s*"
        r"(?:\w+(?:\s*\([^)]*\))?\s*)*"
        r"[{:]{0,1}\s*$"
    )
    for line in changed_lines:
        idx = min(line - 1, len(file_lines) - 1)
        for i in range(idx, -1, -1):
            text = file_lines[i].strip()
            if not text:
                continue
            # Strip inline comments so a line like
            #   "V_MAX = 4.2  # fully charged cell voltage (V)"
            # does not falsely match "voltage".
            code = re.split(r"\s*(?:#|//)", text, maxsplit=1)[0].strip()
            if not code:
                continue
            if re.match(r"^[.\->:]", code):
                continue
            m = sig_re.search(code)
            if m and m.group(1) not in IGNORE_KEYWORDS:
                impacted.add(m.group(1))
                break
    return sorted(impacted)


def _find_enclosing_func_name(file_lines: List[str], line_no: int) -> Optional[str]:
    """Walk backwards from *line_no* to find the enclosing function definition."""
    sig_re = re.compile(
        r"\b([a-zA-Z_]\w*)\s*"
        r"\([^)]*\)\s*"
        r"(?:\w+(?:\s*\([^)]*\))?\s*)*"
        r"[{:]{0,1}\s*$"  # { (C++ body) or : (Python def)
    )
    for i in range(min(line_no, len(file_lines)) - 1, -1, -1):
        text = file_lines[i].strip()
        if not text:
            continue
        # Strip inline comments so "voltage (V)" inside a #-comment is ignored.
        code = re.split(r"\s*(?:#|//)", text, maxsplit=1)[0].strip()
        if not code or re.match(r"^[.\->:]", code):
            continue
        m = sig_re.search(code)
        if m and m.group(1) not in IGNORE_KEYWORDS:
            return m.group(1)
    return None


def _find_cross_file_callers(
    repo: git.Repo,
    commit: Any,
    target_dir: str,
    added_or_modified: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Return entries for source files that call functions changed in
    *added_or_modified*.

    Each returned entry has ``change_type: "I"`` (indirect) and lists the
    *caller-side* function name(s) that contain the call site.

    The search is **transitive**: if ``A`` (changed) is called by ``B``, and
    ``B`` is called by ``C``, both ``B`` and ``C`` are reported. This gives
    languages without a runtime coverage map (C/C++, etc.) a static
    approximation of the deep dependency chains that coverage catches for free.

    To keep the Python (coverage-based) path's behaviour identical, recursion
    only follows **non-Python** callers — Python changes still get a single
    level here and rely on the coverage map for true transitivity.
    """
    # Initial frontier = the directly changed function names.
    frontier: Set[str] = set()
    for item in added_or_modified:
        frontier.update(item.get("impacted_functions", []))

    if not frontier:
        return []

    norm_dir = target_dir.rstrip("/") if target_dir not in (".", "./", "") else ""
    changed_paths: Set[str] = {item["file"] for item in added_or_modified}

    # Read every candidate source file once (path -> lines), so the transitive
    # walk just re-scans this in-memory set instead of re-reading git blobs.
    _skip_ext = {".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg",
                 ".ini", ".png", ".jpg", ".svg", ".ico"}
    files: Dict[str, List[str]] = {}
    for blob in commit.tree.traverse():
        if blob.type != "blob":
            continue
        path = blob.path
        if not path.startswith(norm_dir) or path in changed_paths:
            continue
        if os.path.splitext(path)[1].lower() in _skip_ext:
            continue
        try:
            content = blob.data_stream.read().decode("utf-8", errors="ignore")
        except Exception:
            continue
        files[path] = content.split("\n")

    indirect_map: Dict[str, Set[str]] = {}
    seen_funcs: Set[str] = set(frontier)

    # Fixpoint: expand callers until no new (non-Python) caller is discovered.
    while frontier:
        next_frontier: Set[str] = set()
        for path, file_lines in files.items():
            is_py = path.endswith(".py")
            for fn_name in frontier:
                # One match per function per file is sufficient.
                for i, line in enumerate(file_lines, 1):
                    if re.search(r"\b" + re.escape(fn_name) + r"\s*\(", line):
                        enclosing = _find_enclosing_func_name(file_lines, i)
                        if enclosing and enclosing != fn_name:
                            indirect_map.setdefault(path, set()).add(enclosing)
                            # Only recurse through non-Python callers so the
                            # Python coverage path stays at a single level.
                            if not is_py and enclosing not in seen_funcs:
                                seen_funcs.add(enclosing)
                                next_frontier.add(enclosing)
                        break
        frontier = next_frontier

    return [
        {"file": path, "change_type": "I", "impacted_functions": sorted(fns)}
        for path, fns in indirect_map.items()
    ]


def get_impacted_files(
    repo_path: str,
    base_commit: str,
    target_commit: str = "HEAD",
    target_dir: str = "",
) -> Dict[str, Any]:
    """Analyse base..target and return impacted source files + functions."""
    repo = git.Repo(repo_path)
    commit_a = repo.commit(base_commit)
    commit_b = repo.commit(target_commit)

    diff_index = commit_a.diff(commit_b, create_patch=True)
    result: Dict[str, Any] = {"added_or_modified": [], "deleted": [], "renamed": []}

    norm_dir = target_dir.rstrip("/") if target_dir not in (".", "./", "") else ""

    for item in diff_index:
        a_path = item.a_path or ""
        b_path = item.b_path or ""

        change_type = item.change_type
        if change_type is None:
            if item.new_file:
                change_type = "A"
            elif item.deleted_file:
                change_type = "D"
            elif item.renamed_file:
                change_type = "R"
            else:
                change_type = "M"

        in_scope = (not norm_dir) or a_path.startswith(norm_dir) or b_path.startswith(norm_dir)
        if not in_scope:
            continue

        if change_type in ("A", "M"):
            raw_diff = item.diff.decode("utf-8", errors="ignore") if item.diff else ""
            try:
                blob = commit_b.tree[b_path]
                source = blob.data_stream.read().decode("utf-8", errors="ignore")
            except KeyError:
                source = ""

            file_lines = source.split("\n")
            if change_type == "A":
                # whole new file -> every line is "changed"
                changed_lines = list(range(1, len(file_lines) + 1))
            else:
                changed_lines = _changed_new_lines(raw_diff)

            if b_path.endswith(".py"):
                functions = _python_impacted_functions(source, changed_lines)
            else:
                functions = _regex_impacted_functions(file_lines, changed_lines)

            result["added_or_modified"].append({
                "file": b_path,
                "change_type": change_type,
                "impacted_functions": functions,
            })
        elif change_type == "D":
            result["deleted"].append(a_path)
        elif change_type == "R":
            result["renamed"].append({"old_path": a_path, "new_path": b_path})

    # Cross-file caller analysis: find files that call changed functions.
    if result["added_or_modified"]:
        cross_callers = _find_cross_file_callers(
            repo, commit_b, target_dir, result["added_or_modified"]
        )
        result["added_or_modified"].extend(cross_callers)

    return result
