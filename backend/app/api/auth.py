import requests
from fastapi import APIRouter, HTTPException
from app.schemas.auth import AuthRequest
from app.core.config import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET

router = APIRouter()

@router.post("/github")
async def github_auth(request: AuthRequest):
    """
    Exchange the temporary GitHub OAuth code for a real access token.
    This is a pure in-memory exchange designed for a one-shot execution run.
    """
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=500, 
            detail="GitHub credentials (CLIENT_ID or CLIENT_SECRET) are missing from the environment."
        )

    # Make the exchange request to GitHub
    response = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": request.code
        }
    )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to communicate with GitHub OAuth provider.")

    data = response.json()
    
    # GitHub returns 200 OK even if the code is invalid, but adds an "error" key in the JSON
    if "error" in data:
        raise HTTPException(status_code=400, detail=data.get("error_description", "Invalid OAuth code."))

    # Extract the token
    access_token = data.get("access_token")

    # For this hackathon, we return success and pass the token.
    return {
        "status": "success",
        "message": "Successfully authenticated with GitHub.",
        "access_token": access_token 
    }
