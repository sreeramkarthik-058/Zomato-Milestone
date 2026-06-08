# Multi-stage build for optimized image size
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app/src
ENV PORT=8000

# Copy application code
COPY . .
RUN chmod +x docker-entrypoint.sh

# Pre-download the dataset at build time so the first request is instant
RUN python -c "from src.restaurant_recommender.ingestion.loader import load_raw_dataset; \
    from src.restaurant_recommender.ingestion.normalizer import normalize_rows; \
    from src.restaurant_recommender.store.restaurant_store import RestaurantStore; \
    from pathlib import Path; \
    rows = load_raw_dataset('ManikaSaini/zomato-restaurant-recommendation'); \
    restaurants = normalize_rows(rows); \
    store = RestaurantStore(); \
    store.save_parquet(Path('./data/restaurants.parquet'), restaurants)"

# Expose port (Railway sets PORT env var)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health').read()"

# Use entrypoint script so uvicorn runs as PID 1 and signals are handled correctly
CMD ["./docker-entrypoint.sh"]
