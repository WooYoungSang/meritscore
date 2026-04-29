FROM python:3.11-slim

WORKDIR /app

# Install Node.js 20 (required by python-0g SDK)
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==2.2.1 --no-cache-dir

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (no dev, no virtualenv)
RUN poetry config virtualenvs.create false \
 && poetry install --only main --no-root --no-interaction --no-ansi

# Install ZK proof node dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy source
COPY python/ ./python/
COPY contracts/out/ ./contracts/out/
COPY contracts/abi/ ./contracts/abi/
COPY scripts/ ./scripts/
COPY circuits/merit_threshold_js/ ./circuits/merit_threshold_js/
COPY merit_final.zkey verification_key.json ./
COPY assets/ ./assets/

ENV HOST=0.0.0.0
ENV PORT=61234
ENV MOCK_MODE=false

EXPOSE 61234

CMD ["python", "-m", "uvicorn", "python.bff.main:app", "--host", "0.0.0.0", "--port", "61234"]
