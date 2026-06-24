"""Build the bundled automotive ECU demo repository.

Creates a self-contained git repo (under ``backend/.demo_repo``) with a clean
baseline plus one branch per demo scenario. Each scenario branch is a SINGLE
commit on top of ``base`` so every diff is a clean one-file change:

    base        -> clean baseline, every test green
    safe        -> safe refactor of battery_management.py ......... all tests pass
    regression  -> defect injected into battery_management.compute_soc .. SOC test FAILS
    transitive  -> defect injected into sensor_utils.clamp (a SHARED helper)

The ``transitive`` scenario is the headline for coverage-based selection:
``sensor_utils.py`` is imported by the BMS but is NOT referenced by any test
file. A text/AST matcher would select ZERO tests and skip the bug. The
coverage map (built at the baseline) knows the battery tests actually executed
``clamp()``, so it re-selects them and catches the regression.

Run once before demoing::

    python -m app.demo.setup_demo

Commit hashes are written to ``.demo_repo/commits.json`` and read back by the
/api/analyze/demo endpoint.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
from pathlib import Path

import git


def _force_rmtree(path: Path) -> None:
    """Remove a directory tree, clearing the read-only bit that Windows sets
    on ``.git`` objects (plain shutil.rmtree fails on those)."""
    if not path.exists():
        return

    def _on_error(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)

    try:  # Python 3.12+ uses onexc; older uses onerror
        shutil.rmtree(path, onexc=lambda f, p, e: _on_error(f, p, e))
    except TypeError:
        shutil.rmtree(path, onerror=lambda f, p, e: _on_error(f, p, e))


# backend/app/demo/setup_demo.py -> backend/
BACKEND_ROOT = Path(__file__).resolve().parents[2]
CODEBASE_SRC = Path(__file__).resolve().parent / "codebase"
DEMO_REPO_DIR = BACKEND_ROOT / ".demo_repo"
COMMITS_FILE = DEMO_REPO_DIR / "commits.json"

AUTHOR = git.Actor("SmartTIA Bot", "bot@smarttia.dev")

BMS_FILE = "src/battery_management.py"
UTILS_FILE = "src/sensor_utils.py"

# Safe refactor: a behaviour-preserving edit INSIDE an existing, tested function
# (compute_soc). The battery SOC tests are precisely re-selected and all pass.
SOC_DOC = '"""Estimate State of Charge (%) from a single cell voltage."""'
SOC_DOC_REFACTORED = (
    '"""Estimate State of Charge (%) from a single cell voltage."""\n'
    '    # Refactor: documented linear-interpolation SOC model (no behaviour change).'
)

# Safety-net scenario: add a BRAND-NEW function that no test covers yet. The
# engine can't map it to any test, so it refuses to guess and runs the FULL
# suite -- proving it never silently skips when confidence is low.
SAFE_APPEND = '''

def pack_soc(cell_voltages):
    """Aggregate pack-level SOC as the mean of per-cell SOC estimates."""
    if not cell_voltages:
        return 0.0
    return round(sum(compute_soc(v) for v in cell_voltages) / len(cell_voltages), 2)
'''

# Direct regression: corrupt the SOC interpolation gain in compute_soc itself.
SOC_GOOD = "soc = (v - V_MIN) / (V_MAX - V_MIN) * 100.0  # <<SOC_FORMULA>>"
SOC_BAD = "soc = (v - V_MIN) / (V_MAX - V_MIN) * 10.0  # <<SOC_FORMULA>> (regression)"

# Transitive regression: break the SHARED clamp() helper. No test imports
# sensor_utils, but the battery tests execute clamp() indirectly via compute_soc.
CLAMP_GOOD = """def clamp(value, lo, hi):
    \"\"\"Constrain a value to the inclusive [lo, hi] range.\"\"\"
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value"""
CLAMP_BAD = """def clamp(value, lo, hi):
    \"\"\"Constrain a value to the inclusive [lo, hi] range.\"\"\"
    # regression: lower bound dropped -> compute_soc no longer clamps low voltages
    if value > hi:
        return hi
    return value"""


def _commit_all(repo: git.Repo, message: str) -> str:
    repo.git.add(A=True)
    commit = repo.index.commit(message, author=AUTHOR, committer=AUTHOR)
    return commit.hexsha


def _scenario_branch(repo: git.Repo, base: str, branch: str, rel_file: str,
                     old: str, new: str, message: str) -> str:
    """Create ``branch`` off ``base`` with a single one-file change."""
    repo.git.checkout(base, B=branch)  # create/reset branch at base
    path = DEMO_REPO_DIR / rel_file
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Patch anchor not found in {rel_file}: {old[:40]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")
    sha = _commit_all(repo, message)
    return sha


def _scenario_append(repo: git.Repo, base: str, branch: str, rel_file: str,
                     appended: str, message: str) -> str:
    repo.git.checkout(base, B=branch)
    path = DEMO_REPO_DIR / rel_file
    path.write_text(path.read_text(encoding="utf-8") + appended, encoding="utf-8")
    return _commit_all(repo, message)


def build_demo_repo() -> dict:
    _force_rmtree(DEMO_REPO_DIR)
    DEMO_REPO_DIR.mkdir(parents=True, exist_ok=True)

    # Copy the pristine codebase into the new repo working tree.
    shutil.copytree(CODEBASE_SRC, DEMO_REPO_DIR, dirs_exist_ok=True)

    repo = git.Repo.init(DEMO_REPO_DIR, initial_branch="main")
    base = _commit_all(repo, "feat: baseline ECU control suite (BMS, motor, brake, CAN, diagnostics)")

    safe = _scenario_branch(
        repo, base, "scenario/safe", BMS_FILE, SOC_DOC, SOC_DOC_REFACTORED,
        "refactor(bms): document SOC interpolation model",
    )
    regression = _scenario_branch(
        repo, base, "scenario/regression", BMS_FILE, SOC_GOOD, SOC_BAD,
        "perf(bms): tweak SOC interpolation gain",
    )
    transitive = _scenario_branch(
        repo, base, "scenario/transitive", UTILS_FILE, CLAMP_GOOD, CLAMP_BAD,
        "refactor(utils): simplify clamp() bounds check",
    )
    safety_net = _scenario_append(
        repo, base, "scenario/safety-net", BMS_FILE, SAFE_APPEND,
        "feat(bms): add pack-level SOC aggregation (not yet tested)",
    )

    repo.git.checkout(base)  # leave repo on a clean baseline

    commits = {
        "repo_path": str(DEMO_REPO_DIR),
        "target_dir": "src/",
        "tests_dir": "tests",
        "base": base,
        "scenarios": {
            "safe": {
                "target": safe,
                "label": "Safe refactor",
                "changed": "src/battery_management.py",
                "expectation": "compute_soc edited harmlessly; only its 3 tests re-run, all pass.",
            },
            "regression": {
                "target": regression,
                "label": "Inject regression",
                "changed": "src/battery_management.py",
                "expectation": "compute_soc broken; its tests re-selected and the SOC test catches the bug.",
            },
            "transitive": {
                "target": transitive,
                "label": "Hidden (transitive) bug",
                "changed": "src/sensor_utils.py",
                "expectation": "No test references sensor_utils, yet coverage re-selects the battery tests and catches the bug. Text matching would skip it.",
            },
            "safety_net": {
                "target": safety_net,
                "label": "Untested change (safety net)",
                "changed": "src/battery_management.py",
                "expectation": "A brand-new untested function can't be mapped, so the engine runs the FULL suite rather than risk skipping a defect.",
            },
        },
    }
    COMMITS_FILE.write_text(json.dumps(commits, indent=2), encoding="utf-8")
    repo.close()
    return commits


if __name__ == "__main__":
    info = build_demo_repo()
    print("Demo repo built at:", info["repo_path"])
    print(json.dumps(info, indent=2))
