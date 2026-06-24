from typing import Optional

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    """Analyse an arbitrary Git repository."""
    repo_url: str
    target_commit: str = "HEAD"
    base_commit: Optional[str] = None
    target_dir: str = "src/"
    tests_dir: str = "tests"


class DemoRequest(BaseModel):
    """Run a canned scenario against the bundled automotive ECU repo."""
    scenario: str = "safe"  # "safe" | "regression"
