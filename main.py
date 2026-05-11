from fastapi import FastAPI, Request
from supabase import create_client, Client
import os
import requests

app = FastAPI()

# -----------------------------
# ENVIRONMENT VARIABLES (Railway)
# -----------------------------
SUPABASE_URL = os.getenv("https://eosoiyigcjyjnyfmzqlt.supabase.com")
SUPABASE_KEY = os.getenv("sb_secret_iaPK5KYnH7hknQTQxRPzdg_MNdYn3iu")

TELEGRAM_BOT_TOKEN = os.getenv("8697325888:AAFtrEnNYZOyON9taQvS101gFCFMbl_nkuI")
TELEGRAM_CHAT_ID = os.getenv("cybernews_alertBot")

# -----------------------------
# SUPABASE CLIENT
# -----------------------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# ROOT CHECK
# -----------------------------
@app.get("/")
def root():
    return {"message": "Cyber Threat API Running"}

# -----------------------------
# MAIN WEBHOOK ENDPOINT
# -----------------------------
@app.post("/cybernews")
async def receive_news(request: Request):
    data = await request.json()

    print("Received data:", data)

    # -----------------------------
    # 1. INSERT INTO SUPABASE
    # -----------------------------
    try:
        response = supabase.table("cyber_news").insert(data).execute()
    except Exception as e:
        print("Supabase error:", str(e))
        response = None

    # -----------------------------
    # 2. SEND TELEGRAM ALERT (optional)
    # -----------------------------
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            message = f"🚨 New Cyber News:\n\n{data}"

            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(telegram_url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            })

        except Exception as e:
            print("Telegram error:", str(e))

    # -----------------------------
    # 3. RESPONSE
    # -----------------------------
    return {
        "status": "received",
        "supabase_inserted": True if response else False
    }
  
