# REST API Documentation

## Overview

The Mortgage Rate Notifier REST API provides endpoints for getting trustworthy refinancing decisions with RAG-generated explanations and citations.

**Base URL:** `http://localhost:8000` (or your deployment URL)

**Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## Authentication

Currently, no authentication is required. In production, add API keys:

```bash
# Add to docker-compose.yml or .env
API_KEY_REQUIRED=true
API_KEYS=key1,key2,key3
```

---

## Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

**Description:** Check API health status and system readiness.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000000",
  "rag_system": "ready",
  "uptime_seconds": 3600,
  "version": "1.0.0",
  "environment": "production"
}
```

**Status Codes:**
- `200` - Healthy
- `503` - Degraded (RAG system not loaded)

**Example:**
```bash
curl http://localhost:8000/health
```

---

### 2. Get Trustworthy Decision

**Endpoint:** `POST /decision`

**Description:** Generate a trustworthy refinancing decision for a single user with RAG-generated explanations and citations.

**Request Body:**
```json
{
  "user_data": {
    "id": "USER-001",
    "name": "John Doe",
    "email": "john@example.com",
    "current_rate": 4.5,
    "loan_term_years": 30,
    "monthly_payment": 1200,
    "closing_costs": 5500,
    "credit_score": 750,
    "loan_amount": 350000,
    "remaining_term": 240
  },
  "prediction": {
    "predicted_direction": "DOWN",
    "predicted_average_30d": 4.0,
    "min_rate": 3.9,
    "max_rate": 4.1,
    "confidence": 0.82
  },
  "include_full_report": true
}
```

**Response (200 OK):**
```json
{
  "request_id": "REQ-000001",
  "status": "success",
  "decision": "WAIT 1-2 WEEKS",
  "recommendation": "Wait 1-2 weeks for potentially better rates...",
  "confidence_score": 0.80,
  "confidence_level": "high",
  "explanation": "RECOMMENDATION: Wait 1-2 weeks before refinancing...",
  "citations": [
    {
      "title": "Calculating Break-Even on Refinancing",
      "source": "Consumer Financial Protection Bureau",
      "relevance_score": 0.87,
      "quote": "Break-even analysis helps you determine if refinancing makes financial sense"
    },
    {
      "title": "Understanding Mortgage Refinancing",
      "source": "Federal Reserve",
      "relevance_score": 0.76,
      "quote": "Refinancing involves taking out a new loan to pay off an existing debt"
    }
  ],
  "financial_analysis": {
    "current_rate": 4.5,
    "potential_monthly_saving": 250,
    "breakeven_months": 22,
    "remaining_loan_term_months": 240,
    "closing_costs": 5500,
    "is_financially_safe": true,
    "current_loan_amount": 350000
  },
  "prediction_analysis": {
    "direction": "DOWN",
    "confidence": "82%",
    "average_rate_30d": 4.0,
    "rate_range": "3.9 - 4.1"
  },
  "risk_assessment": "[OK] Low risk - Financial metrics support refinancing",
  "full_report": "======================================================================\nTRUSTWORTHY REFINANCING DECISION REPORT\n...",
  "processing_time_ms": 245.3,
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "detail": "Invalid request: missing required fields"
}
```

**503 Service Unavailable:**
```json
{
  "detail": "RAG system not initialized. Check logs for startup errors."
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/decision \
  -H "Content-Type: application/json" \
  -d @request.json
```

---

### 3. Batch Processing

**Endpoint:** `POST /batch`

**Description:** Process multiple users efficiently in a single request (up to 100 users).

**Request Body:**
```json
{
  "users": [
    {
      "id": "USER-001",
      "name": "John Doe",
      "email": "john@example.com",
      "current_rate": 4.5,
      "loan_term_years": 30,
      "monthly_payment": 1200,
      "closing_costs": 5500,
      "credit_score": 750,
      "loan_amount": 350000,
      "remaining_term": 240
    },
    {
      "id": "USER-002",
      "name": "Jane Smith",
      "email": "jane@example.com",
      "current_rate": 5.0,
      "loan_term_years": 30,
      "monthly_payment": 1400,
      "closing_costs": 6000,
      "credit_score": 720,
      "loan_amount": 400000,
      "remaining_term": 240
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
  ],
  "parallel": false
}
```

**Response (200 OK):**
```json
{
  "batch_id": "BATCH-000001",
  "total_users": 2,
  "successful": 2,
  "failed": 0,
  "processing_time_seconds": 0.85,
  "timestamp": "2024-01-15T10:30:00.000000",
  "results": [
    {
      "request_id": "REQ-000001",
      "status": "success",
      "decision": "WAIT 1-2 WEEKS",
      ...
    },
    {
      "request_id": "REQ-000002",
      "status": "success",
      "decision": "WAIT 1-2 WEEKS",
      ...
    }
  ]
}
```

**Constraints:**
- Maximum 100 users per batch
- Number of users must match number of predictions
- Processing time: ~0.3-0.5s per user

**Example:**
```bash
curl -X POST http://localhost:8000/batch \
  -H "Content-Type: application/json" \
  -d @batch_request.json
```

---

### 4. Metrics

**Endpoint:** `GET /metrics`

**Description:** Get API metrics and statistics.

**Response:**
```json
{
  "timestamp": "2024-01-15T10:30:00.000000",
  "uptime_seconds": 3600,
  "total_requests": 150,
  "status": "healthy",
  "rag_system": "ready"
}
```

**Example:**
```bash
curl http://localhost:8000/metrics
```

---

## Request/Response Models

### UserData

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique user identifier |
| name | string | Yes | User name |
| email | string | No | User email for notifications |
| current_rate | float | Yes | Current mortgage rate (0.1-10.0%) |
| loan_term_years | int | Yes | Original loan term (5-50 years) |
| monthly_payment | float | Yes | Current monthly payment ($) |
| closing_costs | float | Yes | Estimated refinancing costs ($) |
| credit_score | int | Yes | Credit score (300-850) |
| loan_amount | float | No | Loan amount ($) |
| remaining_term | int | No | Remaining loan term (months) |

### PredictionData

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| predicted_direction | string | Yes | UP, DOWN, or STABLE |
| predicted_average_30d | float | Yes | Predicted rate in 30 days (%) |
| min_rate | float | Yes | Minimum predicted rate (%) |
| max_rate | float | Yes | Maximum predicted rate (%) |
| confidence | float | Yes | Model confidence (0.0-1.0) |

### DecisionResponse

| Field | Type | Description |
|-------|------|-------------|
| request_id | string | Unique request identifier |
| status | string | "success" or "error" |
| decision | string | Refinancing recommendation |
| confidence_score | float | Score (0.0-1.0) |
| explanation | string | Personalized explanation |
| citations | array | Financial document citations |
| financial_analysis | object | Break-even, savings, costs |
| risk_assessment | string | Risk factors identified |
| processing_time_ms | float | API response time |
| timestamp | string | ISO 8601 timestamp |

---

## Usage Examples

### Python

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Single decision
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

result = response.json()
print(f"Decision: {result['decision']}")
print(f"Confidence: {result['confidence_score']*100:.0f}%")
print(f"Citations: {len(result['citations'])}")
```

### curl

```bash
# Single decision
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
  }' | python -m json.tool

# Health check
curl http://localhost:8000/health | python -m json.tool
```

### JavaScript/Node.js

```javascript
const BASE_URL = "http://localhost:8000";

async function getDecision(userData, prediction) {
  const response = await fetch(`${BASE_URL}/decision`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      user_data: userData,
      prediction: prediction,
      include_full_report: true
    })
  });

  const result = await response.json();
  return result;
}

// Usage
const user = {
  id: "USER-001",
  name: "John Doe",
  current_rate: 4.5,
  loan_term_years: 30,
  monthly_payment: 1200,
  closing_costs: 5500,
  credit_score: 750
};

const prediction = {
  predicted_direction: "DOWN",
  predicted_average_30d: 4.0,
  min_rate: 3.9,
  max_rate: 4.1,
  confidence: 0.82
};

getDecision(user, prediction).then(decision => {
  console.log(`Decision: ${decision.decision}`);
  console.log(`Citations: ${decision.citations.length}`);
});
```

---

## Error Handling

### Common Errors

**400 Bad Request - Missing Fields:**
```json
{
  "detail": "1 validation error for DecisionRequest\nuser_data.current_rate\n  ensure this value is greater than 0.1 (type=value_error.number.not_gt; limit_value=0.1)"
}
```

**400 Bad Request - Invalid Direction:**
```json
{
  "detail": "1 validation error for PredictionData\nprediction.predicted_direction\n  Direction must be UP, DOWN, or STABLE"
}
```

**503 Service Unavailable:**
```json
{
  "detail": "RAG system not initialized. Check logs for startup errors."
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error"
}
```

---

## Performance

### Latency

| Operation | Time |
|-----------|------|
| Single Decision | 200-400ms |
| Batch 10 Users | 1-2 seconds |
| Batch 100 Users | 30-50 seconds |

### Throughput

- **Concurrent Requests:** Unlimited (FastAPI/uvicorn handles async)
- **Batch Size:** 1-100 users per request
- **API Calls:** ~5-10 per user (cached when possible)

### Resource Usage

- **Memory Base:** ~200MB
- **Per Concurrent Request:** ~10MB
- **Logs:** ~1MB per 1,000 decisions

---

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run API
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

### Docker

```bash
# Build image
docker build -t mortgage-notifier-api .

# Run container
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-xxxx \
  mortgage-notifier-api
```

### Docker Compose

```bash
# Set environment variables
export OPENAI_API_KEY=sk-xxxx

# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

---

## Rate Limiting (Future)

Rate limiting can be added with:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/decision")
@limiter.limit("100/minute")
async def get_decision(request: DecisionRequest):
    ...
```

---

## Monitoring

Monitor these metrics:
- Request count and rate
- Response time (p50, p95, p99)
- Error rate
- RAG system status
- Memory and CPU usage

Tools:
- Prometheus + Grafana
- DataDog
- New Relic
- AWS CloudWatch

---

## Support

For issues, check:
1. API logs: `docker-compose logs api`
2. Health endpoint: `GET /health`
3. Swagger docs: `http://localhost:8000/docs`

---

## Changelog

### v1.0.0 (2024-01-15)
- Initial REST API launch
- Single decision endpoint
- Batch processing support
- Full OpenAPI documentation
- Docker containerization

---

**Ready to use!** Start the API and visit http://localhost:8000/docs for interactive documentation.
