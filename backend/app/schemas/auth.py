from pydantic import BaseModel

class AuthRequest(BaseModel):
    code: str
