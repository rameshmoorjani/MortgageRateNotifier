# 🚀 Getting Started with Mortgage Rate Notifier API

The simplest way to start using the API. Choose your preferred method below.

---

## ⚡ Quick Start (30 seconds)

### Option 1: Test Health Check (No Setup)

```bash
curl https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "Mortgage Rate Notifier",
  "version": "1.0.0"
}
```

✅ **Done!** API is live and working.

---

## 🔧 Option 2: Use cURL (Linux/macOS/Windows PowerShell)

### Analyze a Single Mortgage Decision

```bash
curl -X POST https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/decision \
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
      "confidence": 0.82
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "user_id": "USER-001",
  "decision": {
    "recommendation": "MARGINAL",
    "monthly_saving": 50.00,
    "breakeven_months": 110,
    "confidence": 0.82
  }
}
```

---

## 🐍 Option 3: Use Python (Easiest)

### 1. Install Python SDK

```bash
# Basic request (no installation needed)
pip install requests  # if not already installed
```

### 2. Write Your First Script

```python
import requests
import json

# API endpoint
API_URL = "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev"

# Mortgage data
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
        "confidence": 0.82
    }
}

# Make request
response = requests.post(
    f"{API_URL}/decision",
    json=request_data,
    headers={"Content-Type": "application/json"}
)

# Print result
result = response.json()
print(json.dumps(result, indent=2))
```

### 3. Run It

```bash
python your_script.py
```

---

## 📮 Option 4: Use Postman (GUI - No Coding)

### 1. Download Postman
https://www.postman.com/downloads/

### 2. Import Collection
- Open Postman
- Click **Import** → **Upload Files**
- Select `Mortgage_Rate_Notifier_API.postman_collection.json` from this repo
- All endpoints pre-configured!

### 3. Test Endpoints
- Expand collection in left sidebar
- Click any request (e.g., "Analyze Single Mortgage")
- Click **Send**
- See response on the right

---

## 📊 Real-World Examples

### Example 1: Strong Refinancing Opportunity

Current rate 5.5% → Predicted 4.0% (1.5% drop) = Monthly savings: $187.50

```bash
curl -X POST https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/decision \
  -H "Content-Type: application/json" \
  -d '{
    "user_data": {
      "id": "USER-STRONG",
      "name": "Sarah",
      "current_rate": 5.5,
      "loan_term_years": 30,
      "monthly_payment": 1500,
      "closing_costs": 5500,
      "credit_score": 780
    },
    "prediction": {
      "predicted_direction": "DOWN",
      "predicted_average_30d": 4.0,
      "confidence": 0.87
    }
  }'
```

**Result:** `STRONGLY_RECOMMENDED` ✅  
**Breakeven:** 29 months

---

### Example 2: Avoid Refinancing

Rates predicted to RISE (3.5% → 4.5%) = Don't refinance

```bash
curl -X POST https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/decision \
  -H "Content-Type: application/json" \
  -d '{
    "user_data": {
      "id": "USER-AVOID",
      "name": "Mike",
      "current_rate": 3.5,
      "loan_term_years": 30,
      "monthly_payment": 900,
      "closing_costs": 5500,
      "credit_score": 720
    },
    "prediction": {
      "predicted_direction": "UP",
      "predicted_average_30d": 4.5,
      "confidence": 0.91
    }
  }'
```

**Result:** `NOT_RECOMMENDED` ❌

---

## 🔄 Batch Processing (Analyze 100+ Users)

Process multiple users in one request. Great for banks/lenders analyzing portfolios.

### Python Example

```python
import requests

API_URL = "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev"

# Multiple users
users = [
    {
        "user_data": {"id": "USER-001", "name": "Alice", "current_rate": 5.5, ...},
        "prediction": {"predicted_direction": "DOWN", "predicted_average_30d": 4.0, ...}
    },
    {
        "user_data": {"id": "USER-002", "name": "Bob", "current_rate": 4.5, ...},
        "prediction": {"predicted_direction": "DOWN", "predicted_average_30d": 4.0, ...}
    },
    # ... up to 100 users
]

# Send batch
response = requests.post(
    f"{API_URL}/batch",
    json=users
)

# Get results
results = response.json()
for result in results['results']:
    print(f"{result['user_id']}: {result['recommendation']}")
```

---

## 📋 API Endpoints Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check API status |
| `/metrics` | GET | Get usage stats |
| `/decision` | POST | Analyze single mortgage |
| `/batch` | POST | Analyze up to 100 users |

---

## 🎯 Request Body Reference

### Single Decision (POST /decision)

```json
{
  "user_data": {
    "id": "unique-user-id",
    "name": "User Name",
    "current_rate": 4.5,           // Current mortgage rate (%)
    "loan_term_years": 30,         // Loan term (years)
    "monthly_payment": 1200,       // Monthly payment ($)
    "closing_costs": 5500,         // Refinancing costs ($)
    "credit_score": 750            // Credit score (300-850)
  },
  "prediction": {
    "predicted_direction": "DOWN",  // "DOWN", "UP", or "STABLE"
    "predicted_average_30d": 4.0,   // Predicted avg rate in 30 days (%)
    "confidence": 0.82              // Confidence (0.0 to 1.0)
  }
}
```

### Batch (POST /batch)

```json
[
  { "user_data": {...}, "prediction": {...} },
  { "user_data": {...}, "prediction": {...} },
  ...up to 100
]
```

---

## 📊 Response Format

### Success Response

```json
{
  "success": true,
  "user_id": "USER-001",
  "decision": {
    "recommendation": "MARGINAL|RECOMMENDED|STRONGLY_RECOMMENDED|NOT_RECOMMENDED",
    "monthly_saving": 50.00,        // Monthly savings ($)
    "breakeven_months": 110,        // Months to break even
    "confidence": 0.82              // Confidence score
  },
  "market_prediction": {
    "direction": "DOWN",
    "predicted_rate": 4.0,
    "confidence": 0.82
  },
  "analysis": {
    "current_rate": 4.5,
    "predicted_rate": 4.0,
    "rate_difference": 0.5
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": "Invalid rate range",
  "details": "Current rate must be between 2.0 and 8.0"
}
```

---

## 💡 Tips & Tricks

### 1. Pretty Print JSON (cURL)

```bash
curl ... | jq .
```

### 2. Save Request to File

```bash
curl ... > result.json
```

### 3. Test with Different Scenarios

Try different rate directions to see recommendations:
- **DOWN (rates falling):** More likely to recommend refinancing
- **UP (rates rising):** Will avoid recommending unless already great deal
- **STABLE (rates flat):** Depends on closing costs vs savings

### 4. Loop Through Multiple Users (Bash)

```bash
for i in {1..10}; do
  curl -X POST https://... -d "{\"user_data\": {\"id\": \"USER-$i\", ...}}"
done
```

### 5. Python: Analyze Your Portfolio

```python
import requests
import pandas as pd

# Your customers
customers = pd.read_csv('customers.csv')

# Analyze each
results = []
for _, customer in customers.iterrows():
    response = requests.post(
        'https://.../decision',
        json={
            "user_data": customer.to_dict(),
            "prediction": get_prediction()  # use FRED API or your own model
        }
    )
    results.append(response.json())

# Export results
pd.DataFrame(results).to_csv('decisions.csv')
```

---

## 🆘 Troubleshooting

| Error | Solution |
|-------|----------|
| `Status 400: Invalid request` | Check JSON format, all fields required |
| `Status 500: Server error` | API may be experiencing issues; check health endpoint |
| `Status 413: Payload too large` | Batch size >100 users; split into smaller batches |
| `Slow response (>2s)` | Normal for cold Lambda starts; usually <500ms after |

---

## 📚 Next Steps

1. **Test Health Check:** `curl .../health`
2. **Try Single Decision:** Use cURL example above
3. **Automate:** Build batch processing script
4. **Integrate:** Add to your app or workflow
5. **Provide Feedback:** Report issues on GitHub

---

## 🔗 Resources

- **GitHub Repo:** https://github.com/rameshmoorjani/MortgageRateNotifier
- **Full API Docs:** See `API_TESTING_GUIDE.md`
- **Technical Deep Dive:** See `RATE_CALCULATION_EXPLAINED.md`
- **Architecture:** See `PORTFOLIO_SHOWCASE.md`

---

## 💬 Support

- **Issues:** https://github.com/rameshmoorjani/MortgageRateNotifier/issues
- **Questions:** Open a GitHub discussion
- **Email:** support@mortgagenotifier.com

---

**Ready to try it?** Start with `curl https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/health` 🚀
