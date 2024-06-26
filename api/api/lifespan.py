from contextlib import asynccontextmanager
from typing import AsyncIterator

from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI

from api.settings import ELASTIC_SETTINGS


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    es_client = AsyncElasticsearch(
        ELASTIC_SETTINGS.url, basic_auth=(ELASTIC_SETTINGS.username, ELASTIC_SETTINGS.password)
    )

    app.state.es_client = es_client

    yield

    await es_client.close()
