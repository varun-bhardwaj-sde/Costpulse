FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-interaction --no-root --only main 2>/dev/null || pip install fastapi uvicorn sqlalchemy asyncpg pydantic pydantic-settings structlog

COPY . .
RUN pip install -e .

EXPOSE 8000

CMD ["uvicorn", "costpulse.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
