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
