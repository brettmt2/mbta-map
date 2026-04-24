from contextlib import asynccontextmanager
from fastapi import FastAPI
import httpx

client: httpx.AsyncClient = None

@asynccontextmanager
async def lifespan(_: FastAPI):
    # load the httpx context manager
    global client
    client = httpx.AsyncClient()

    yield
    
    await client.aclose()

app = FastAPI(lifespan=lifespan)

