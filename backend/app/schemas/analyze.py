from typing import Optional

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    """Analyse an arbitrary Git repository."""
    repo_url: str
    target_commit: str = "HEAD"
    base_commit: Optional[str] = None
    target_dir: str = "src/"
    tests_dir: str = "tests"
    github_token: Optional[str] = None


class MapRequest(BaseModel):
    """Lightweight static analysis: diff + test mapping without test execution."""
    repo_url: str
    target_commit: str = "HEAD"
    base_commit: Optional[str] = None
    source_dir: str = "src/"
    tests_dir: str = "tests"
    github_token: Optional[str] = None


class DemoRequest(BaseModel):
    """Run a canned scenario against the bundled automotive ECU repo."""
    scenario: str = "safe"  # "safe" | "regression"
