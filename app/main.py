from fastapi import FastAPI, Query, Depends
from .config import get_settings, Settings

app = FastAPI(title="TEST")


@app.get("/ping")
async def pong(settings: Settings = Depends(get_settings)):
    return {"ping": "pong!",
            "environment": settings.environment,
            "testing": settings.testing}
