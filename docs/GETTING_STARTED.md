# Getting Started - 5 Minute Setup

Get the Mortgage Rate Notifier API running in 5 minutes.

---

## Step 1: Prerequisites (1 minute)

**You need:**
- Docker (download: https://www.docker.com/products/docker-desktop)
- OpenAI API Key (free trial: https://platform.openai.com)

**Verify installation:**
```bash
docker --version
docker-compose --version
```

---

## Step 2: Set API Key (1 minute)

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY = "sk-xxxxxxxxxxxx"
```

**Linux/macOS (Bash):**
```bash
export OPENAI_API_KEY="sk-xxxxxxxxxxxx"
```

Replace `sk-xxxxxxxxxxxx` with your actual OpenAI API key.

---

## Step 3: Start the API (1 minute)

```bash
cd c:\Users\rames\projects\MortgageRateNotifier
docker-compose up
```

Wait for this message:
```
api  | INFO:     Uvicorn running on http://0.0.0.0:8000
api  | INFO:     Application startup complete
```

---

## Step 4: Test It Works (1 minute)

**Option A: Health Check**
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "rag_system": "ready"
}
```

**Option B: Interactive UI**
Open browser to: **http://localhost:8000/docs**

You'll see Swagger UI with all endpoints and live examples.

**Option C: Run Test Suite**
```bash
# In another terminal
python test_api.py
```

Expected output:
```
✓ PASSED: API is reachable
✓ PASSED: Status is 'healthy'
✓ PASSED: RAG system is 'ready'
...
All tests PASSED!
```

---

## Step 5: Make Your First Request (1 minute)

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

**Expected response (reformatted):**
```json
{
  "request_id": "REQ-000001",
  "status": "success",
  "decision": "WAIT 1-2 WEEKS",
  "confidence_score": 0.80,
  "explanation": "RECOMMENDATION: Wait 1-2 weeks recommending...",
  "citations": [
    {
      "title": "Calculating Break-Even on Refinancing",
      "source": "Consumer Financial Protection Bureau",
      "relevance_score": 0.87
    },
    {
      "title": "Understanding Mortgage Refinancing",
      "source": "Federal Reserve",
      "relevance_score": 0.76
    }
  ],
  "financial_analysis": {
    "current_rate": 4.5,
    "potential_monthly_saving": 250,
    "breakeven_months": 22,
    "is_financially_safe": true
  },
  "processing_time_ms": 245.3
}
```

---

## Done! ✅

Your API is now running and ready to use.

---

## Common Commands

| Goal | Command |
|------|---------|
| Start API | `docker-compose up` |
| Stop API | `Ctrl+C` (or `docker-compose down` in another terminal) |
| View logs | `docker-compose logs -f api` |
| Run tests | `python test_api.py` |
| API documentation | Visit http://localhost:8000/docs |
| Health check | `curl http://localhost:8000/health` |

---

## What to Do Next

### ✅ Try the Interactive UI
1. Open http://localhost:8000/docs
2. Click "Try it out" on any endpoint
3. Fill in parameters
4. Click "Execute"

### ✅ Process Multiple Users
1. Use `/batch` endpoint to process 1-100 users at once
2. See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for examples

### ✅ Integrate with Your App
1. See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for code examples
2. Python, JavaScript, curl examples included

### ✅ Deploy to Production
1. See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for cloud deployment
2. Supports Heroku, Railway, AWS, GCP, Azure

---

## Troubleshooting

### ❌ "Cannot connect to http://localhost:8000"

**Solution:** Ensure API is running
```bash
# Terminal 1 - Start API
docker-compose up

# Terminal 2 - Test
curl http://localhost:8000/health
```

### ❌ "RAG system not initialized"

**Solution 1:** Wait 30 seconds for startup
```bash
# Check logs for "RAG system loaded"
docker-compose logs api | grep RAG
```

**Solution 2:** Verify OpenAI API key
```bash
# Make sure your API key is set
echo $OPENAI_API_KEY  # Linux/macOS
echo $env:OPENAI_API_KEY  # PowerShell
```

### ❌ "Port 8000 already in use"

**Solution:** Change the port in docker-compose.yml
```yaml
# Change this line:
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

Then visit: http://localhost:8001

### ❌ Tests Failed

**Solution:** Run with verbose output
```bash
python test_api.py --verbose
```

Check logs:
```bash
docker-compose logs api
```

---

## API Overview

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check API status |
| `/decision` | POST | Single refinancing decision |
| `/batch` | POST | Process multiple users |
| `/metrics` | GET | Performance metrics |
| `/docs` | GET | Interactive Swagger UI |

### Response Time

- Single decision: **200-400ms**
- Batch 10 users: **1-2 seconds**
- Batch 100 users: **30-50 seconds**

### Features

✅ Trustworthy AI decisions with citations  
✅ Financial break-even analysis  
✅ Market prediction integration  
✅ Batch processing support  
✅ High confidence scores  
✅ Risk assessment  
✅ Full transparency  

---

## Documentation

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [README.md](README.md) | System overview | 5 min |
| **This file** | Quick setup | 5 min |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Complete API reference | 10 min |
| [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) | Docker & deployment | 15 min |
| [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) | Production setup | 20 min |

---

## Quick Reference

### Single Decision Request
```json
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
```

### Batch Request
```json
{
  "users": [
    {...user1...},
    {...user2...}
  ],
  "predictions": [
    {...prediction1...},
    {...prediction2...}
  ]
}
```

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for full details and examples.

---

## Key Features Explained

### 🤖 Trustworthy AI
Every decision includes:
- Personalized explanation
- Financial document citations
- Confidence score (0-100%)
- Risk assessment
- Complete financial analysis

### 💰 Financial Analysis
Automatically calculates:
- Break-even timeline
- Monthly savings potential
- Remaining loan term
- Risk level (Low/Medium/High)
- Financial safety assessment

### 📊 Market Intelligence
Integrates with:
- Rate direction prediction (UP/DOWN/STABLE)
- Predicted average rate in 30 days
- Rate range scenarios
- Confidence scoring

### ⚡ Performance
- Fast responses (200-400ms)
- Handles 100+ users efficiently
- Scales with Docker
- Production-ready

---

## Support

**Having issues?**

1. Check the troubleshooting section above
2. Run `python test_api.py --verbose` for details
3. Check logs: `docker-compose logs api`
4. Review [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
5. See [DOCKER_DEPLOYMENT.md#troubleshooting](DOCKER_DEPLOYMENT.md)

---

**You're all set!** 🎉

Start building with the API. Visit http://localhost:8000/docs to explore all endpoints.

---

## What's Next?

1. ✅ API running locally
2. → Integrate with your application
3. → Deploy to production (Heroku/Railway/AWS)
4. → Add database for persistence
5. → Setup monitoring and alerting

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for production deployment steps.

---

**Questions?** Check the comprehensive documentation in [API_DOCUMENTATION.md](API_DOCUMENTATION.md) or [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md).

**Ready to deploy?** Follow [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for cloud setup.
