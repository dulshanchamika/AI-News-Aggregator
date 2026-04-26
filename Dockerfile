FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy everything FIRST so uv can see the project structure
COPY . .

# Now install. Use --no-dev to keep the image slim (skip jupyter/ipykernel)
RUN uv sync --frozen --no-dev

# Fix the CMD typo (comma instead of dot)
CMD ["sh", "-c", "python -m app.database.create_tables || true && python main.py"]