import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv("e:\\Projects\\medpredict\\.env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)
try:
    res = supabase.table("predictions").select("id, predicted_disease, risk_level, confidence_score, honesty_flag, mri_consistency, health_score, created_at").limit(1).execute()
    print("predictions success:", res.data)
except Exception as e:
    print("predictions error:", str(e))

try:
    res2 = supabase.table("insurance_price_predictions").select("id, annual_premium, monthly_premium, premium_band, region, age, smoker, created_at").limit(1).execute()
    print("insurance success:", res2.data)
except Exception as e:
    print("insurance error:", str(e))
