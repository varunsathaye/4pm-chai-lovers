from __future__ import annotations

import shutil
import tempfile
from typing import Any, Dict, Optional

import git

from app.services import diff_analyzer, test_mapper, timing_service


def map_impact(
    repo_source: str,
    target_commit: str,
    base_commit: Optional[str] = None,
    source_dir: str = "src/",
    tests_dir: str = "tests",
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    work_dir = tempfile.mkdtemp(prefix="smarttia_map_")
    try:
        clone_url = repo_source
        if github_token and "github.com" in repo_source:
            clone_url = repo_source.replace(
                "https://github.com/", f"https://x-access-token:{github_token}@github.com/"
            )

        repo = git.Repo.clone_from(clone_url, work_dir)

        target_sha = repo.commit(target_commit).hexsha

        if base_commit:
            base_sha = repo.commit(base_commit).hexsha
        else:
            commit_obj = repo.commit(target_sha)
            base_sha = commit_obj.parents[0].hexsha if commit_obj.parents else commit_obj.hexsha

        # Use the service-level AST-based diff analyzer (handles Python correctly)
        diff_data = diff_analyzer.get_impacted_files(
            work_dir, base_sha, target_sha, target_dir=source_dir
        )

        impacted_items = diff_data.get("added_or_modified", [])

        # Use the service-level AST-based test mapper
        mapping = test_mapper.map_tests(
            diff_data, work_dir, target_sha, tests_dir_prefix=tests_dir
        )

        # Collect all test files in the repo for the full-suite overview.
        try:
            all_paths = repo.git.ls_tree("-r", "--name-only", target_sha).splitlines()
        except git.exc.GitCommandError:
            all_paths = []
        all_test_files = sorted(
            p for p in all_paths
            if p.startswith(tests_dir) and p.split(".")[-1].lower()
            in {"py", "c", "cc", "cpp", "cxx", "h", "hpp", "hxx", "js", "ts",
                "jsx", "tsx", "java", "kt", "go", "rs", "rb", "swift", "sh", "bash"}
        )

        # Read test timings from tests/test_timings.json (if present).
        timings = timing_service.read_test_timings(work_dir, target_sha, tests_dir)
        timing_metrics = timing_service.compute_timing_metrics(
            timings,
            mapping["selected_test_files"],
            len(mapping["selected_test_files"]),
        )

        all_modified = [i["file"] for i in impacted_items]
        all_functions = []
        for i in impacted_items:
            for fn in i.get("impacted_functions", []):
                all_functions.append(f"{i['file']}::{fn}")

        return {
            "status": "success",
            "commit": {
                "hash": target_sha[:7],
                "base": base_sha[:7],
            },
            "diff_summary": {
                "modified_files": all_modified,
                "impacted_functions": sorted(set(all_functions)),
                "total_changed": len(all_modified),
            },
            "test_mapping": {
                "selected_test_files": mapping["selected_test_files"],
                "by_source": mapping["by_source"],
                "total_impacted_test_files": len(mapping["selected_test_files"]),
            },
            "all_test_files": all_test_files,
            "timing": timing_metrics,
            "source_dir": source_dir,
            "tests_dir": tests_dir,
        }

    except git.exc.GitCommandError as e:
        return {"status": "error", "detail": f"Git error: {e}"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
