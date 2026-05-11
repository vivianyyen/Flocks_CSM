from fastapi import FastAPI
from pydantic import BaseModel
from supabase import create_client, Client
import requests
import os

app = FastAPI()

# =========================
# 1. SUPABASE CONFIG
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# 2. TELEGRAM CONFIG (optional)
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def send_telegram(message: str):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message
    })


# =========================
# 3. DATA MODEL (Flocks JSON)
# =========================
class NewsItem(BaseModel):
    title: str
    publication_date: str
    source: str
    url: str
    summary: str
    relevant_keywords: list


# =========================
# 4. INSERT INTO SUPABASE
# =========================
def insert_news(item: NewsItem):

    data = {
        "title": item.title,
        "publication_date": item.publication_date,
        "source": item.source,
        "url": item.url,
        "summary": item.summary,
        "relevant_keywords": ",".join(item.relevant_keywords)
    }

    response = supabase.table("cyber_news").insert(data).execute()
    return response


# =========================
# 5. MAIN INGEST ENDPOINT (FLOCKS CALLS THIS)
# =========================
@app.post("/ingest")
def ingest_news(item: NewsItem):

    result = insert_news(item)

    # optional: trigger alert
    send_telegram(f"🚨 New Cyber News:\n{item.title}")

    return {
        "status": "success",
        "message": "stored in supabase"
    }


# =========================
# 6. HEALTH CHECK
# =========================
@app.get("/")
def home():
    return {"status": "API running"}
