import os

from fastapi import FastAPI, Query, Depends
from .config import get_settings, Settings
from tortoise.contrib.fastapi import register_tortoise
app = FastAPI(title="TEST")
register_tortoise(
    app,
    db_url=os.environ.get("DATABASE_URL"),
    modules={"models": ["app.models.tortoise"]},
    generate_schemas=False,
    add_exception_handlers=True,
)


@app.get("/ping")
async def pong(settings: Settings = Depends(get_settings)):
    return {"ping": "pong!",
            "environment": settings.environment,
            "testing": settings.testing}
