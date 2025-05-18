from fastapi import APIRouter, HTTPException
from backend.models.schemas import LoginRequest
from backend.core.supabase import supabase

router = APIRouter()

@router.post("/login")
async def login_user(credentials: LoginRequest):
    response = supabase.auth.sign_in_with_password({
        "email": credentials.email,
        "password": credentials.password
    })

    if response.user is None:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")

    return {
        "status": "success",
        "user": {
            "id": response.user.id,
            "email": response.user.email
        }
    }
