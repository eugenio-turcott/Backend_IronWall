from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os
from dotenv import load_dotenv
load_dotenv()

ALGORITHM = "HS256"

SECRET_KEY = os.getenv("SUPABASE_JWT_SECRET")

security = HTTPBearer()

def get_curr_user(token: HTTPAuthorizationCredentials, algorithms=[ALGORITHM]):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token",
        )