FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir \
    fastapi \
    pika \
    pydantic-settings \
    uvicorn


COPY app ./app

CMD ["python", "-m", "app.main"]
