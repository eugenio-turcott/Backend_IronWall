from supabase import create_client, Client
from core.config import SUPABASE_URL, SUPABASE_API_KEY

if SUPABASE_URL is None or SUPABASE_API_KEY is None:
    raise ValueError("Supabase URL and API key must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)