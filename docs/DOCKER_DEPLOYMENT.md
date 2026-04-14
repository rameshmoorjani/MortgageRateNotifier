# Docker Deployment & Quick Start Guide

This guide walks you through building, testing, and deploying the Mortgage Rate Notifier API using Docker.

---

## Prerequisites

- Docker (v20.10+): https://docs.docker.com/get-docker/
- Docker Compose (v2.0+): Usually included with Docker Desktop
- OpenAI API Key: https://platform.openai.com/api-keys

**Verify Installation:**
```bash
docker --version
docker-compose --version
```

---

## Quick Start (5 minutes)

### 1. Set Your API Key

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY = "sk-xxxxxxxxxxxx"
```

**Linux/macOS (Bash):**
```bash
export OPENAI_API_KEY="sk-xxxxxxxxxxxx"
```

### 2. Start the API

```bash
cd c:\Users\rames\projects\MortgageRateNotifier
docker-compose up
```

You'll see:
```
api  | INFO:     Started server process
api  | INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. Test the API

**Option A: Health Check**
```bash
curl http://localhost:8000/health
```

**Option B: Interactive Swagger UI**
Open browser to: http://localhost:8000/docs

**Option C: Fast Test Script**
```bash
python test_api.py
```

### 4. Get a Decision

**Using curl:**
```bash
curl -X POST http://localhost:8000/decision \
  -H "Content-Type: application/json" \
  -d '{
    "user_data": {
      "id": "USER-001",
      "name": "John Doe",
      "current_rate": 4.5,
      "loan_term_years": 30,
      "monthly_payment": 1200,
      "closing_costs": 5500,
      "credit_score": 750
    },
    "prediction": {
      "predicted_direction": "DOWN",
      "predicted_average_30d": 4.0,
      "min_rate": 3.9,
      "max_rate": 4.1,
      "confidence": 0.82
    }
  }'
```

### 5. Stop the API

```bash
# Press Ctrl+C in terminal, or in another terminal:
docker-compose down
```

---

## Building the Docker Image

### Build Locally

```bash
docker build -t mortgage-notifier:latest .
```

**Output:**
```
[+] Building 45.2s (10/10) FINISHED
 => [internal] load build context
 => => transferring context: 125MB
 => [1/9] FROM python:3.11-slim
 => [2/9] WORKDIR /app
 => ...
 => => naming to docker.io/library/mortgage-notifier:latest
```

### Build with Docker Compose

```bash
# Rebuild image
docker-compose build

# Start services
docker-compose up
```

### Verify Build

```bash
docker images | grep mortgage-notifier
# Output: mortgage-notifier  latest  abc123def456  2 minutes ago  1.2GB
```

---

## Running the Container

### Using Docker Directly

**Start:**
```bash
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-xxxx \
  -v logs:/app/logs \
  --name mortgage-api \
  mortgage-notifier:latest
```

**Check Status:**
```bash
docker ps -a | grep mortgage-api
```

**View Logs:**
```bash
docker logs -f mortgage-api
```

**Stop:**
```bash
docker stop mortgage-api
docker rm mortgage-api
```

### Using Docker Compose (Recommended)

**Start:**
```bash
docker-compose up -d
```

**Status:**
```bash
docker-compose ps
```

**Logs:**
```bash
# All services
docker-compose logs -f

# Just API
docker-compose logs -f api
```

**Stop:**
```bash
docker-compose down
```

**Restart:**
```bash
docker-compose restart api
```

---

## Testing the API

### Test Script

Create `test_api.py`:
```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✓ Health check passed")

def test_single_decision():
    request_data = {
        "user_data": {
            "id": "USER-001",
            "name": "John Doe",
            "current_rate": 4.5,
            "loan_term_years": 30,
            "monthly_payment": 1200,
            "closing_costs": 5500,
            "credit_score": 750
        },
        "prediction": {
            "predicted_direction": "DOWN",
            "predicted_average_30d": 4.0,
            "min_rate": 3.9,
            "max_rate": 4.1,
            "confidence": 0.82
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/decision",
        json=request_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "decision" in data
    assert "citations" in data
    assert len(data["citations"]) > 0
    print(f"✓ Single decision test passed")
    print(f"  Decision: {data['decision']}")
    print(f"  Confidence: {data['confidence_score']*100:.0f}%")
    print(f"  Citations: {len(data['citations'])}")

def test_batch():
    request_data = {
        "users": [
            {
                "id": "USER-001",
                "name": "John Doe",
                "current_rate": 4.5,
                "loan_term_years": 30,
                "monthly_payment": 1200,
                "closing_costs": 5500,
                "credit_score": 750
            },
            {
                "id": "USER-002",
                "name": "Jane Smith",
                "current_rate": 5.0,
                "loan_term_years": 30,
                "monthly_payment": 1400,
                "closing_costs": 6000,
                "credit_score": 720
            }
        ],
        "predictions": [
            {
                "predicted_direction": "DOWN",
                "predicted_average_30d": 4.0,
                "min_rate": 3.9,
                "max_rate": 4.1,
                "confidence": 0.82
            },
            {
                "predicted_direction": "DOWN",
                "predicted_average_30d": 4.0,
                "min_rate": 3.9,
                "max_rate": 4.1,
                "confidence": 0.82
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/batch",
        json=request_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 2
    assert data["successful"] == 2
    print(f"✓ Batch test passed ({data['successful']}/{data['total_users']} users)")

if __name__ == "__main__":
    try:
        test_health()
        test_single_decision()
        test_batch()
        print("\n" + "="*50)
        print("All tests passed! API is working correctly.")
        print("="*50)
    except Exception as e:
        print(f"✗ Test failed: {e}")
        raise
```

**Run:**
```bash
python test_api.py
```

### Manual Testing with curl

**Health:**
```bash
curl http://localhost:8000/health | python -m json.tool
```

**Single Decision:**
```bash
curl -X POST http://localhost:8000/decision \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "user_data": {
    "id": "USER-001",
    "name": "John Doe",
    "current_rate": 4.5,
    "loan_term_years": 30,
    "monthly_payment": 1200,
    "closing_costs": 5500,
    "credit_score": 750
  },
  "prediction": {
    "predicted_direction": "DOWN",
    "predicted_average_30d": 4.0,
    "min_rate": 3.9,
    "max_rate": 4.1,
    "confidence": 0.82
  }
}
EOF
```

**Metrics:**
```bash
curl http://localhost:8000/metrics
```

---

## Troubleshooting

### API Won't Start

**Check logs:**
```bash
docker-compose logs api
```

**Common Issues:**

| Error | Solution |
|-------|----------|
| `Port 8000 already in use` | `docker ps` to find container, then `docker stop <id>` |
| `ModuleNotFoundError: openai` | Rebuild image: `docker-compose build --no-cache` |
| `RAG system not initialized` | Check OpenAI API key: `docker-compose logs api \| grep OPENAI` |

### Connection Refused

```bash
# Is container running?
docker-compose ps

# Try connecting with more details
curl -vv http://localhost:8000/health

# Check Docker network
docker-compose ps
docker network ls
```

### Out of Memory

```bash
# Check container memory
docker stats mortgage-notifier_api

# Increase in docker-compose.yml (deploy.resources.limits.memory)
```

---

## Production Deployment

### Environment Variables

Create `.env` file:
```
OPENAI_API_KEY=sk-xxxxxxxxxxxx
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=production
```

Then start:
```bash
docker-compose --env-file .env up -d
```

### Resource Allocation

In `docker-compose.yml`, adjust for your needs:
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'      # 2 CPU cores
          memory: 4G     # 4GB RAM
        reservations:
          cpus: '1'
          memory: 2G
```

### Restart Policy

```yaml
services:
  api:
    restart_policy:
      condition: unless-stopped
      delay: 5s
      max_attempts: 5
      window: 120s
```

### Health Checks

Docker automatically monitors with:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

---

## Cloud Deployment

### Heroku

```bash
# Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Create app
heroku create mortgage-notifier-api

# Set environment variable
heroku config:set OPENAI_API_KEY=sk-xxxx

# Push Docker image
heroku container:push web
heroku container:release web

# View logs
heroku logs --tail

# Visit app
heroku open
```

### Railway

```bash
# Install Railway CLI
# https://railway.app/help#railway-cli

# Create project
railway init

# Link Dockerfile
# Set OPENAI_API_KEY in dashboard

# Deploy
railway up

# View logs
railway logs

# Get URL
railway domain
```

### AWS (ECR + ECS)

```bash
# Create ECR repository
aws ecr create-repository --repository-name mortgage-notifier

# Get login token
aws ecr get-login-password | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.REGION.amazonaws.com

# Tag image
docker tag mortgage-notifier:latest ACCOUNT.dkr.ecr.REGION.amazonaws.com/mortgage-notifier:latest

# Push
docker push ACCOUNT.dkr.ecr.REGION.amazonaws.com/mortgage-notifier:latest

# Create ECS task and service...
```

---

## Monitoring

### Docker Stats

```bash
# Real-time statistics
docker stats mortgage-notifier_api
```

### Logs Analysis

```bash
# Last 50 lines
docker-compose logs --tail 50 api

# Follow logs
docker-compose logs -f api

# Save logs to file
docker-compose logs api > api.log
```

### Health Dashboard

Visit: `http://localhost:8000/docs` for interactive API docs with request/response examples.

---

## Scaling

### Multiple API Instances (Load Balanced)

Create `docker-compose-scale.yml`:
```yaml
version: '3.9'

services:
  api-1:
    image: mortgage-notifier:latest
    ports:
      - "8001:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}

  api-2:
    image: mortgage-notifier:latest
    ports:
      - "8002:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api-1
      - api-2

networks:
  default:
    name: mortgage-network
```

Start:
```bash
docker-compose -f docker-compose-scale.yml up -d
```

---

## Cleanup

### Remove Container

```bash
docker-compose down
```

### Remove Image

```bash
docker rmi mortgage-notifier:latest
```

### Remove All (Caution!)

```bash
docker-compose down -v  # Also removes volumes
docker system prune -a   # Remove unused images
```

---

## Next Steps

1. ✅ Start API: `docker-compose up`
2. ✅ Test API: Visit http://localhost:8000/docs
3. ✅ Monitor: `docker-compose logs -f`
4. → Add database (PostgreSQL) for persistence
5. → Deploy to cloud (Heroku/Railway/AWS)
6. → Add monitoring (Prometheus + Grafana)
7. → Add authentication (API keys)
8. → Setup CI/CD (GitHub Actions)

---

**You're ready to go!** Start with `docker-compose up` and visit http://localhost:8000/docs
