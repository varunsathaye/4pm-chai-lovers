"""Build the bundled automotive ECU demo repository.

Creates a self-contained git repo (under ``backend/.demo_repo``) with three
commits that drive the live demo:

    base        -> clean baseline, every test green
    safe        -> a safe refactor of battery_management.py (BMS) ............ all green
    regression  -> a real defect injected into battery_management.compute_soc  battery test FAILS

Because all three commits touch only ``src/battery_management.py``, Smart-TIA
selects exactly the battery test module in both scenarios. The point of the
demo is the contrast:

  * safe scenario       -> selected subset runs fast and stays green
  * regression scenario -> selected subset still CATCHES the bug
                           (we never skipped the test that mattered)

Run it once before demoing::

    python -m app.demo.setup_demo

The resulting commit hashes are written to ``.demo_repo/commits.json`` and read
back by the /api/analyze/demo endpoint.
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

# A safe refactor: append a pure helper. Behaviour of existing functions is
# unchanged, so all battery tests still pass -- but the file is modified, so
# Smart-TIA correctly re-selects the battery test module.
SAFE_APPEND = '''

def pack_soc(cell_voltages):
    """Aggregate pack-level SOC as the mean of per-cell SOC estimates."""
    if not cell_voltages:
        return 0.0
    return round(sum(compute_soc(v) for v in cell_voltages) / len(cell_voltages), 2)
'''

# The regression: corrupt the SOC interpolation gain. compute_soc(3.6) now
# returns ~5.0 instead of 50.0, so test_compute_soc_midpoint fails -- exactly
# the kind of silent measurement bug TIA must never skip over.
SOC_GOOD = "(cell_voltage - V_MIN) / (V_MAX - V_MIN) * 100.0  # <<SOC_FORMULA>>"
SOC_BAD = "(cell_voltage - V_MIN) / (V_MAX - V_MIN) * 10.0  # <<SOC_FORMULA>> (regression)"


def _commit_all(repo: git.Repo, message: str) -> str:
    repo.git.add(A=True)
    commit = repo.index.commit(message, author=AUTHOR, committer=AUTHOR)
    return commit.hexsha


def build_demo_repo() -> dict:
    _force_rmtree(DEMO_REPO_DIR)
    DEMO_REPO_DIR.mkdir(parents=True, exist_ok=True)

    # Copy the pristine codebase into the new repo working tree.
    shutil.copytree(CODEBASE_SRC, DEMO_REPO_DIR, dirs_exist_ok=True)

    repo = git.Repo.init(DEMO_REPO_DIR)
    base = _commit_all(repo, "feat: baseline ECU control suite (BMS, motor, brake, CAN, diagnostics)")

    # --- safe refactor ---
    bms_path = DEMO_REPO_DIR / BMS_FILE
    bms_path.write_text(bms_path.read_text(encoding="utf-8") + SAFE_APPEND, encoding="utf-8")
    safe = _commit_all(repo, "refactor(bms): add pack-level SOC aggregation helper")

    # --- inject regression ---
    text = bms_path.read_text(encoding="utf-8").replace(SOC_GOOD, SOC_BAD)
    bms_path.write_text(text, encoding="utf-8")
    regression = _commit_all(repo, "perf(bms): tweak SOC interpolation gain")

    commits = {
        "repo_path": str(DEMO_REPO_DIR),
        "target_dir": "src/",
        "tests_dir": "tests",
        "base": base,
        "scenarios": {
            "safe": {
                "target": safe,
                "label": "Safe refactor",
                "expectation": "Battery tests re-selected; all pass.",
            },
            "regression": {
                "target": regression,
                "label": "Inject regression",
                "expectation": "Battery tests re-selected; SOC test catches the bug.",
            },
        },
    }
    COMMITS_FILE.write_text(json.dumps(commits, indent=2), encoding="utf-8")
    return commits


if __name__ == "__main__":
    info = build_demo_repo()
    print("Demo repo built at:", info["repo_path"])
    print(json.dumps(info, indent=2))
