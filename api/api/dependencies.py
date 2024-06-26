from typing import Annotated

from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from starlette.requests import Request


async def _get_es_client(request: Request) -> AsyncElasticsearch:
    return request.app.state.es_client


ElasticClientDep = Annotated[AsyncElasticsearch, Depends(_get_es_client)]
