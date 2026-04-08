FROM python:3.11-slim

LABEL maintainer="NeuroHack"
LABEL description="SQL Debugger & Optimizer — OpenEnv"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt .
COPY pyproject.toml .
COPY uv.lock .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project structure
COPY server/ ./server/
COPY sql_debugger_env.py .
COPY openenv.yaml .
COPY inference.py .
COPY README.md .

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# 🔥 IMPORTANT CHANGE
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]