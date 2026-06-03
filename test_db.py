import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv("e:\\Projects\\medpredict\\.env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("Error: Missing SUPABASE_URL or SUPABASE_KEY in .env")
    exit(1)

try:
    supabase: Client = create_client(url, key)
    # Test a simple query
    res = supabase.table("predictions").select("id").limit(1).execute()
    print("Successfully connected to Supabase and queried predictions table.")
    print("Result:", res.data)
except Exception as e:
    print("Error connecting to Supabase or querying:", str(e))
