from contextlib import asynccontextmanager
from fastapi import FastAPI
import httpx
import json

import os
from dotenv import load_dotenv

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import redis

from app.mbta import get_line_times

load_dotenv(override=False)

client: httpx.AsyncClient = None
r: redis.Redis = None

@asynccontextmanager
async def lifespan(_: FastAPI):
    # load the httpx context manager
    global client
    client = httpx.AsyncClient()

    # load Redis manager
    global r
    host = os.getenv('REDIS_HOST')
    port = int(os.getenv('REDIS_PORT'))
    password = os.getenv('REDIS_PASSWORD')
    r = redis.Redis(host=host, port=port, password=password, decode_responses=True)

    yield
    
    await client.aclose()
    r.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://mbta-map.up.railway.app"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/times/{line_color}")
async def get_times(line_color: str):
    cached = r.get(f'data-{line_color}')

    if cached:
        return json.loads(cached)

    try:
        data = await get_line_times(client=client, color=line_color)
        r.setex(f'data-{line_color}', 60, json.dumps(data))
        return data
    except Exception as e:
        print(f'Error fetching data for {line_color}: {e}')
        stale = r.get(f'data-{line_color}')
        return json.loads(stale) if stale else {}

app.mount("/", StaticFiles(directory="web", html=True), name="web")