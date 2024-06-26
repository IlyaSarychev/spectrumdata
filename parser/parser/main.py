import argparse
import asyncio
import hashlib
from asyncio import Queue, TimeoutError
from functools import partial
from parser.settings import ELASTIC_SETTINGS
from typing import Any, NamedTuple
from urllib.parse import urlparse

from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup
from elasticsearch import AsyncElasticsearch, RequestError
from loguru import logger


class Page(NamedTuple):
    url: str
    depth: int


async def _init_es_index(es_client: AsyncElasticsearch) -> None:
    if not await es_client.indices.exists(index=ELASTIC_SETTINGS.index):
        logger.debug(f"Индекс {ELASTIC_SETTINGS.index} не существует. Создаем..")
        await es_client.indices.create(
            index=ELASTIC_SETTINGS.index,
            settings={
                "analysis": {"analyzer": {"html_stripper": {"tokenizer": "standard", "char_filter": ["html_strip"]}}}
            },
            mappings={"properties": {"content": {"type": "text", "analyzer": "html_stripper"}}},
        )


async def _send_result_to_elastic(es_client: AsyncElasticsearch, url: str, title: str, content: str) -> None:
    try:
        await es_client.index(
            index=ELASTIC_SETTINGS.index,
            id=hashlib.sha256(url.encode("utf-8")).hexdigest(),
            document={"title": title, "url": url, "content": content},
        )
    except RequestError as err:
        logger.opt(exception=True).error(f"Произошла некорректная отправка страницы в ES {err}")
        raise
    except Exception as err:
        logger.opt(exception=True).error(f"Произошла непредвиденная ошибка во время отправки страницы в ES {err}")
    else:
        logger.success(f"Отправка в Elasticsearch страницы {url} прошла успешно")


async def _parse_page(pages: Queue[Page], max_depth: int, es_client: AsyncElasticsearch, in_progress: set[str]) -> None:
    async with ClientSession() as session:
        while True:
            try:
                url, depth = await asyncio.wait_for(pages.get(), timeout=25)
            except TimeoutError:
                logger.info(f"Не было получено новых страниц в течение 25 секунд. Завершаем задачу")
                return

            if url in in_progress:
                continue

            if depth > max_depth:
                logger.info(f"Страница {url} не будет обработана. Максимальная глубина парсинга - {max_depth}")
                continue

            in_progress.add(url)

            try:
                async with session.get(url, timeout=ClientTimeout(connect=20), ssl=False) as resp:
                    html = await resp.text()
            except TimeoutError as err:
                logger.error(f"При получении страницы {url} произошел таймаут (20 секунд): {err}")
                continue
            except Exception as err:
                logger.opt(exception=True).error(f"При получении страницы {url} произошла непредвиденная ошибка: {err}")
                continue

            soup = BeautifulSoup(html, "html.parser")
            title = (soup.title.string if soup.title.string else "") if soup.title else ""
            logger.info(f"Получена страница. Глубина: {depth}. Заголовок: {title}")

            for a in soup.find_all("a"):
                anchor_href = a.get("href")
                if not anchor_href:
                    continue

                processing_url = urlparse(url)
                anchor_url = urlparse(anchor_href)

                if not (
                    anchor_url.hostname == processing_url.hostname
                    or anchor_href.startswith("/")
                    and not anchor_href.startswith("//")
                ):
                    continue

                next_url = f"{processing_url.scheme}://{processing_url.netloc}{anchor_url.path}"

                await pages.put(Page(next_url, depth + 1))

            try:
                await _send_result_to_elastic(
                    es_client=es_client,
                    url=url,
                    title=title,
                    content=str(soup),
                )
            except Exception:
                continue


async def main(url: str, max_workers: int, max_depth: int) -> None:
    pages_queue: Queue[Page] = Queue()

    es_client = AsyncElasticsearch(
        ELASTIC_SETTINGS.url, basic_auth=(ELASTIC_SETTINGS.username, ELASTIC_SETTINGS.password)
    )

    await _init_es_index(es_client=es_client)

    in_progress: set[str] = set()
    parse_future = asyncio.gather(
        *(
            _parse_page(pages=pages_queue, max_depth=max_depth, es_client=es_client, in_progress=in_progress)
            for _ in range(max_workers)
        )
    )

    await pages_queue.put(Page(url, 0))
    await parse_future

    await es_client.close()


if __name__ == "__main__":

    def _limited_int_type(x: Any, from_: int, to_: int | None = None) -> int:
        x = int(x)
        if x < from_:
            raise argparse.ArgumentTypeError(f"Значение аргумента должно быть не менее {from_}")
        if to_ is not None and x > to_:
            raise argparse.ArgumentTypeError(f"Значение аргумента должно быть не более {to_}")
        return x

    parser = argparse.ArgumentParser(description="Парсинг сайта с последующей записью в Elasticsearch")
    parser.add_argument("url", type=str, help="Ссылка на сайт")
    parser.add_argument(
        "--max_workers",
        type=partial(_limited_int_type, from_=1, to_=10),
        default=4,
        help="Макс. кол-во одновременно обрабатываемых страниц от 1 до 10 (По умолчанию 4)",
    )
    parser.add_argument(
        "--depth",
        type=partial(_limited_int_type, from_=0),
        default=2,
        help="Глубина обхода сайта от 0 (По умолчанию 2). При значении 0 будет обработана только переданная страница",
    )
    args = parser.parse_args()

    logger.debug(f"Парсинг сайта {args.url} в глубину {args.depth}. Кол-во тасок: {args.max_workers}")

    asyncio.run(
        main(
            url=args.url,
            max_workers=args.max_workers,
            max_depth=args.depth,
        )
    )
