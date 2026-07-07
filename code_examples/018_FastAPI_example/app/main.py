from fastapi import FastAPI

from .routers import tasks

app = FastAPI(
    title="Tasks API",
    description="Task management CRUD API",
    version="0.0.1"
    )

app.include_router(tasks.router)

@app.get(
    "/",
    tags=["root"],
    summary="API Root"
    )
def read_root():
    return {"message": "Tasks API running"}
