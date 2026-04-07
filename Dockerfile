FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl \
    && rm -rf /var/lib/apt/lists/*

# Install OpenEnv core + dependencies
RUN pip install --no-cache-dir \
    openenv-core \
    fastapi \
    uvicorn \
    openai \
    pydantic

# Copy project files
COPY . .

# Install project as package (picks up pyproject.toml if present)
RUN pip install --no-cache-dir -e . 2>/dev/null || true

# HuggingFace Spaces listens on port 7860
EXPOSE 7860

# Environment variable defaults (overridden at runtime)
ENV API_BASE_URL="https://router.huggingface.co/v1"
ENV MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
ENV PORT=7860

# Start FastAPI server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
