from fastapi import FastAPI
from fastapi import Request

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Cyber Threat API Running"}

@app.post("/cybernews")
async def cybernews(request: Request):

    data = await request.json()

    print(data)

    return {
        "status": "received",
        "data": data
    }
    
import requests

TELEGRAM_TOKEN = "8697325888:AAFtrEnNYZOyON9taQvS101gFCFMbl_nkuI"
CHAT_ID = "1812439245"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=data)
    @app.get("/alert")
    
def alert():
    send_telegram("New cyber news detected!")
    return {"status": "sent"}
