# Deployment Guide

## Docker (Recommended)

```bash
cp .env.example .env
# Edit .env with your API keys

docker-compose up -d
```

This starts:
- **Aegis** on port 8000
- **Redis** on port 6379
- **Prometheus** on port 9090
- **Grafana** on port 3000 (admin password: `aegis`)

## Manual Installation

```bash
# Python 3.11+ required
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start Redis separately
redis-server &

# Configure
cp .env.example .env
# Edit .env

# Run
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## VPS Deployment (8GB RAM)

Minimum requirements:
- 2 CPU cores
- 8GB RAM (embedding model uses ~200MB, total service <1.5GB)
- 10GB disk

```bash
# Install dependencies
apt update && apt install python3.11 python3.11-venv redis-server -y

# Clone and setup
git clone https://github.com/gauthamhk/aegis.git
cd aegis
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env

# Run with systemd or pm2
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| GEMINI_API_KEY | Yes | | Google Gemini API key |
| GROQ_API_KEY | No | | Groq API key |
| OPENROUTER_API_KEY | No | | OpenRouter API key |
| REDIS_URL | No | redis://localhost:6379 | Redis connection URL |
| DATABASE_URL | No | sqlite:///./data/aegis.db | SQLite database path |
| EMBEDDING_MODEL | No | all-MiniLM-L6-v2 | Sentence transformer model |
| DEFAULT_DOMAIN | No | general | Default domain config |
| LOG_LEVEL | No | INFO | Logging level |
| MAX_CONCURRENT_VERIFICATIONS | No | 50 | Max parallel verifications |
| ENTROPY_SAMPLE_COUNT | No | 5 | Responses to generate for entropy |
