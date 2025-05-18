from fastapi import APIRouter, HTTPException
from models.schemas import LoginRequest
from core.supabase import supabase

router = APIRouter()

@router.post("/login")
async def login_user(credentials: LoginRequest):
    response = supabase.auth.sign_in_with_password({
        "email": credentials.email,
        "password": credentials.password
    })

    if response.user is None:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")
    
    # Obtener datos adicionales del usuario desde la tabla 'profiles'
    user_data = supabase.table('profiles').select(
        "full_name, role, subrole, avatar_url"
    ).eq('id', response.user.id).single().execute()

    return {
        "status": "success",
        "access_token":response.session.access_token,
        "refresh_token":response.session.refresh_token,
        "user": {
            "id": response.user.id,
            "email": response.user.email,
            "full_name": user_data.data.get('full_name'),
            "role": user_data.data.get('role'),
            "subrole": user_data.data.get('subrole'),
            "avatar_url": user_data.data.get('avatar_url')
        }
    }
