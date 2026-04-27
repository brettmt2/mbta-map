from contextlib import asynccontextmanager
from fastapi import FastAPI
import httpx

from fastapi.middleware.cors import CORSMiddleware

from app.mbta import get_line_times

import os


client: httpx.AsyncClient = None

@asynccontextmanager
async def lifespan(_: FastAPI):
    # load the httpx context manager
    global client
    client = httpx.AsyncClient()

    yield
    
    await client.aclose()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/times/{line_color}")
async def get_times(line_color: str):
    return await get_line_times(client=client, color=line_color)

@app.get("/debug")
async def debug():
    key = os.getenv("API_KEY")
    return {
        "client_alive": client is not None,
        "api_key_set": key is not None,
        "api_key_preview": key[:6] + "..." if key else None
    }

def get_headers():
    return {
        'accept': 'application/vnd.api+json',
        'x-api-key': os.getenv('API_KEY')
    }

@app.get("/ping-mbta")
async def ping_mbta():
    res = await client.get("https://api-v3.mbta.com/routes", headers=get_headers())
    return {"status": res.status_code, "body_preview": res.text[:300]}
