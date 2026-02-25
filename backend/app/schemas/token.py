from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    expires_in: int

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
