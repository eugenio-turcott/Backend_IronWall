from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase config
# ----------------------- Cambiar esto a .env próximamente -----------------------
SUPABASE_URL = "https://aavyrfxfbcwodyfcjmjr.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFhdnlyZnhmYmN3b2R5ZmNqbWpyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDczNTQ1MzMsImV4cCI6MjA2MjkzMDUzM30.I98bA3l25hbQFSp0OEbKziwaI6HOr4GlWS_a7ZqJ_u8"
supabase: Client =  create_client(SUPABASE_URL, SUPABASE_API_KEY)

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/login")
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
