from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import analyze, auth

app = FastAPI(title="SmartTIA Engine API")

# Configure CORS to allow requests from the Vite frontend default port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "SmartTIA Engine"}


# Include Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["Analysis"])
