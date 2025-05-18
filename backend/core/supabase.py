from supabase import create_client, Client
from backend.core.config import SUPABASE_URL, SUPABASE_API_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)