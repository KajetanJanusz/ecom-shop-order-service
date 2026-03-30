from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import user_router
from core.broker.client import get_broker_client


@asynccontextmanager
async def lifespan(_):
    broker_client = get_broker_client()
    await broker_client.connect()
    yield
    await broker_client.disconnect()


def create_app() -> FastAPI:
    app_ = FastAPI(
        title="Ecom Shop Order Service",
        description="Order service for ecom shop",
        version="1.0.0",
        lifespan=lifespan,
    )
    app_.include_router(user_router)
    return app_


app = create_app()
