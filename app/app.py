from contextlib import asynccontextmanager
from fastapi import FastAPI
import httpx

import sys
sys.path.append(".")

from app.mbta import get_line_times

client: httpx.AsyncClient = None

@asynccontextmanager
async def lifespan(_: FastAPI):
    # load the httpx context manager
    global client
    client = httpx.AsyncClient()

    yield
    
    await client.aclose()

app = FastAPI(lifespan=lifespan)

@app.get("/times/{line_color}")
async def get_times(line_color: str):
    return await get_line_times(client=client, color=line_color)

