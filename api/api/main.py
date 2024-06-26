from typing import Any

from fastapi import FastAPI, Query

from api.dependencies import ElasticClientDep
from api.lifespan import lifespan
from api.schemas import Page, PageShortInfo
from api.settings import ELASTIC_SETTINGS

app = FastAPI(lifespan=lifespan)


@app.get("/pages/search")
async def get_pages(
    es_client: ElasticClientDep,
    title: str | None = None,
    url: str | None = None,
    page: int = Query(1, gt=0),
    size: int = Query(20, gt=0),
) -> list[PageShortInfo]:
    matches = {key: value for key, value in {"title": title, "url": url}.items() if value}
    query: dict[str, Any] = {"match_all": {}}

    if matches:
        query = {"bool": {"must": [{"match": {key: value}} for key, value in matches.items()]}}

    from_ = (page - 1) * size

    resp = await es_client.search(index=ELASTIC_SETTINGS.index, query=query, from_=from_, size=size)

    return [PageShortInfo(**hit["_source"], id=hit["_id"]) for hit in resp["hits"]["hits"]]


@app.get("/pages/{page_id}")
async def get_page(es_client: ElasticClientDep, page_id: str) -> Page:
    resp = await es_client.get(
        index=ELASTIC_SETTINGS.index,
        id=page_id,
    )

    return Page(**resp["_source"], id=resp["_id"])
