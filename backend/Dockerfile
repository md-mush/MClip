# Use Python 3.11 slim image
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy pyproject.toml and uv.lock for dependency installation
COPY pyproject.toml uv.lock* ./

# Install uv and use it to create venv and install dependencies PROPERLY
RUN pip install uv && \
    uv venv .venv && \
    # Use the system uv to install into the venv
    uv pip install --python /app/.venv/bin/python -r pyproject.toml

# Copy source code
COPY src/ ./src/

# Create necessary directories
RUN mkdir -p /app/uploads /app/temp /app/outputs /app/logs

# Set Python path
ENV PYTHONPATH=/app/src

# Expose the port FastAPI will run on
EXPOSE 8000

# Use the uvicorn binary directly from virtual environment
CMD ["/app/.venv/bin/uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]