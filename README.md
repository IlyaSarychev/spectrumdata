# Тестовое задание: парсер сайта + API

Начало работы:
```shell
DOCKER_BUILDKIT=0 docker compose build

docker compose up -d api elastic
```

---
Запуск парсера:
```shell
docker compose run --rm -it parser https://scpfoundation.net/
```

Дополнительные параметры:

- --max_workers - макс. кол-во одновременно обрабатываемых страниц от 1 до 10 (По умолчанию 4)
- --depth - глубина обхода сайта от 0 (По умолчанию 2). При значении 0 будет обработана только переданная страница

Открыть Swagger [тык](http://localhost:8000/docs)