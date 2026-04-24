FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry==2.2.1 --no-cache-dir

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (no dev, no virtualenv)
RUN poetry config virtualenvs.create false \
 && poetry install --only main --no-root --no-interaction --no-ansi

# Copy source
COPY python/ ./python/
COPY contracts/out/ ./contracts/out/

ENV HOST=0.0.0.0
ENV PORT=61234
ENV MOCK_MODE=false

EXPOSE 61234

CMD ["python", "-m", "uvicorn", "python.bff.main:app", "--host", "0.0.0.0", "--port", "61234"]
