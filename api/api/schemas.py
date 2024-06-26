from pydantic import BaseModel, HttpUrl


class PageShortInfo(BaseModel):
    id: str
    title: str
    url: HttpUrl


class Page(PageShortInfo):
    content: str
