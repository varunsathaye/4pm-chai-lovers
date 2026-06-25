"""Analysis endpoints: the heart of the Smart-TIA engine.

* POST /api/analyze        -> run on any Git repo (URL + commit)
* POST /api/analyze/demo   -> run a canned scenario on the bundled ECU repo
"""
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.demo.setup_demo import COMMITS_FILE, build_demo_repo
from app.schemas.analyze import AnalyzeRequest, DemoRequest, MapRequest
from app.services import pipeline, simple_mapper

router = APIRouter()


@router.post("/map")
async def analyze_map(request: MapRequest):
    """Lightweight static mapping: diff source_dir and map to tests_dir.
    Does NOT execute any tests — just shows you which test files are
    impacted by the changes in the given commit range.
    """
    result = simple_mapper.map_impact(
        repo_source=request.repo_url,
        target_commit=request.target_commit,
        base_commit=request.base_commit,
        source_dir=request.source_dir,
        tests_dir=request.tests_dir,
        github_token=request.github_token,
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["detail"])
    return result


@router.post("")
async def analyze(request: AnalyzeRequest):
    """Run Smart-TIA against an arbitrary repository."""
    try:
        return pipeline.run_analysis(
            repo_source=request.repo_url,
            target_commit=request.target_commit,
            base_commit=request.base_commit,
            target_dir=request.target_dir,
            tests_dir=request.tests_dir,
            github_token=request.github_token,
        )
    except Exception as exc:  # noqa: BLE001 - surface a clean error to the UI
        raise HTTPException(status_code=400, detail=f"Analysis failed: {exc}")


def _load_demo_config() -> dict:
    """Load (or build on first use) the bundled demo repo commit metadata."""
    if not COMMITS_FILE.exists():
        return build_demo_repo()
    return json.loads(Path(COMMITS_FILE).read_text(encoding="utf-8"))


@router.post("/demo")
async def analyze_demo(request: DemoRequest):
    """Run a pre-built scenario (safe refactor / injected regression)."""
    config = _load_demo_config()
    scenarios = config["scenarios"]
    if request.scenario not in scenarios:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario '{request.scenario}'. Choose one of {list(scenarios)}.",
        )

    scenario = scenarios[request.scenario]
    try:
        result = pipeline.run_analysis(
            repo_source=config["repo_path"],
            target_commit=scenario["target"],
            base_commit=config["base"],
            target_dir=config["target_dir"],
            tests_dir=config["tests_dir"],
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Demo analysis failed: {exc}")

    result["scenario"] = {
        "key": request.scenario,
        "label": scenario["label"],
        "expectation": scenario["expectation"],
    }
    return result


@router.get("/demo/scenarios")
async def demo_scenarios():
    """List available demo scenarios (used to render the demo buttons)."""
    config = _load_demo_config()
    return {
        key: {"label": val["label"], "expectation": val["expectation"]}
        for key, val in config["scenarios"].items()
    }
