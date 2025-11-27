FROM python:3.11-slim as base

# Install system dependencies
RUN apt update && apt install -y curl

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app
COPY pyproject.toml poetry.lock ./

FROM base as development

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-interaction

# Create data directories
RUN mkdir -p /app/data/inbound /app/data/outbound

# Set working directory
WORKDIR /app