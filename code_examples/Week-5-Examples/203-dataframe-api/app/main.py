"""FastAPI app entry point.

Wires the router in and warms the DataFrame cache at startup so the CSV is read
exactly once for the life of the process.

Run from the demo folder:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import services
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    services.load_data()      # read + prep the DataFrame before serving traffic
    yield


app = FastAPI(
    title="DataFrame API",
    description="Serves pandas-computed aggregates from a CSV as JSON.",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "rows": len(services.load_data())}
