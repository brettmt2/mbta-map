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
