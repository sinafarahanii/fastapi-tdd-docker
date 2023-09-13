from fastapi import FastAPI
from app.api import api_handler
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware import Middleware


def create_application() -> FastAPI:
    application = FastAPI(title="Task")
    application.include_router(api_handler.router)
    return application


app = create_application()