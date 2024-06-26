FROM python:3.10-slim as stage0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_HOME=/opt/poetry \
    POETRY_VERSION=1.8.0

ENV APP_DIR=/app

ENV PATH="$POETRY_HOME/bin:$PATH"
ENV PYTHONPATH=$PYTHONPATH:$APP_DIR

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        curl \
        build-essential

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR $APP_DIR

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-dev

COPY api $APP_DIR/api

FROM stage0 as test

RUN poetry install --no-interaction --no-ansi --only=dev

COPY Makefile ./

RUN make BIN_DIR=/usr/local/bin lint

FROM stage0 as final

ENTRYPOINT ["fastapi", "run", "api/main.py"]