from fastapi import FastAPI
from supabase import create_client

app = FastAPI()

@app.post("/cybernews")
async def receive_news(data: dict):

    print(data)

    # insert into database
    # send telegram alert

    return {"status": "received"}
