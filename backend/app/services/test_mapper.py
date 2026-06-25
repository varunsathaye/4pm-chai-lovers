"""Map impacted source code to the test files that exercise it.

For Python test files we parse the AST and extract:
  * the modules they import      (``from src.battery_management import ...``)
  * every identifier they reference (function/attribute names)

For non-Python test files we extract includes and identifiers via regex.

A test is mapped to an impacted source file when it imports/includes that
module *or* references one of the specific functions the diff flagged as
changed.  When AST/regex matching misses, a whole-word keyword fallback
scan ensures we never under-select.
"""
from __future__ import annotations

import ast
import os
import re
from typing import Any, Dict, List, Set, Union

import git


# File extensions treated as testable source code.
_TEST_EXTENSIONS = {
    ".py", ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hxx",
    ".js", ".ts", ".jsx", ".tsx",
    ".java", ".kt", ".scala",
    ".go", ".rs", ".rb", ".swift",
    ".sh", ".bash",
}

# C++ / common-language keywords that must never be reported as a
# "referenced identifier" for matching purposes.
_KEYWORD_SET = {
    "if", "for", "while", "switch", "catch", "else", "return",
    "public", "private", "protected", "class", "struct", "namespace",
    "template", "typename", "constexpr", "const", "const_cast",
    "static_cast", "dynamic_cast", "reinterpret_cast", "sizeof",
    "typeid", "decltype", "throw", "try", "new", "delete",
    "using", "typedef", "extern", "static", "volatile", "mutable",
    "virtual", "override", "final", "noexcept", "explicit",
    "inline", "export", "friend", "auto", "register", "unsigned",
    "signed", "short", "long", "int", "float", "double", "char",
    "bool", "void", "wchar_t", "size_t", "int8_t", "uint8_t",
    "int16_t", "uint16_t", "int32_t", "uint32_t", "int64_t", "uint64_t",
    "nullptr", "true", "false", "this", "operator",
    "import", "from", "def", "async", "await", "lambda",
    "assert", "raise", "except", "finally", "with", "yield",
    "describe", "it", "beforeEach", "afterEach", "beforeAll", "afterAll",
    "var", "let", "function",
}


def _is_test_file(path: str) -> bool:
    """Return True if *path* looks like a testable source file."""
    _, ext = os.path.splitext(path)
    return ext.lower() in _TEST_EXTENSIONS


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
    """Return (imported_module_basenames, referenced_identifiers)
    using the Python AST.
    """
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


def _generic_test_symbols(source: str) -> tuple[Set[str], Set[str]]:
    """Return (imported_module_basenames, referenced_identifiers)
    for arbitrary source code via lightweight regex.

    *imported* captures:
      - ``#include`` / ``#import`` filenames (stripped of path/extension)
      - ``using namespace X``
      - ``using X::``
    *referenced* captures every identifier-like token (words that aren't
    language keywords).
    """
    imported: Set[str] = set()
    referenced: Set[str] = set()

    # --- includes ---
    for m in re.finditer(
        r'#\s*(?:include|import)\s+[<"]([^>"]+)[>"]',
        source,
        re.MULTILINE,
    ):
        inc = m.group(1)
        name = os.path.splitext(os.path.basename(inc))[0]
        if name:
            imported.add(name)

    # --- using namespace / using X::Y ---
    for m in re.finditer(
        r'\busing\s+(?:namespace\s+)?([a-zA-Z_]\w*)',
        source,
    ):
        imported.add(m.group(1))

    # --- every identifier-like token ---
    for m in re.finditer(r'\b([a-zA-Z_]\w*)\b', source):
        token = m.group(1)
        if token not in _KEYWORD_SET:
            referenced.add(token)

    return imported, referenced


def map_tests(
    diff_data: Dict[str, Any],
    repo_path: str,
    target_commit: str,
    tests_dir_prefixes: Union[str, List[str]] = "tests",
) -> Dict[str, Any]:
    """Return mapping of impacted source files -> impacted test files.

    Shape::

        {
          "selected_test_files": ["tests/test_battery_management.py", ...],
          "by_source": {"src/battery_management.py": ["tests/test_..."], ...},
        }
    """
    if isinstance(tests_dir_prefixes, str):
        tests_dir_prefixes = [tests_dir_prefixes]

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
        if not (any(path.startswith(d) for d in tests_dir_prefixes) and _is_test_file(path)):
            continue

        content = blob.data_stream.read().decode("utf-8", errors="ignore")

        if path.endswith(".py"):
            imported, referenced = _python_test_symbols(content)
        else:
            imported, referenced = _generic_test_symbols(content)

        for source_file, meta in index.items():
            module = meta["module"]
            funcs = meta["functions"]
            hit = (module in imported) or bool(funcs & referenced)
            if not hit:
                # Fall back to whole-word keyword scan so we never under-select.
                # Check the module name first, then each impacted function name.
                if re.search(r"\b" + re.escape(module) + r"\b", content):
                    hit = True
                elif funcs:
                    for fn in funcs:
                        if re.search(r"\b" + re.escape(fn) + r"\b", content):
                            hit = True
                            break
            if hit:
                by_source[source_file].append(path)
                selected.add(path)

    return {
        "selected_test_files": sorted(selected),
        "by_source": {k: sorted(v) for k, v in by_source.items()},
    }
