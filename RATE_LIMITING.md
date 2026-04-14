# 🚦 Rate Limiting Documentation

Your Mortgage Rate Notifier API now has **rate limiting** enabled to protect against abuse and excessive requests.

---

## 📊 Rate Limits by Endpoint

| Endpoint | Method | Limit | Purpose |
|----------|--------|-------|---------|
| `/` | GET | 60/minute | Root information endpoint |
| `/health` | GET | 60/minute | Health checks |
| `/decision` | POST | 30/minute | Single refinancing decision |
| `/batch` | POST | 10/minute | Batch user processing (more resource-intensive) |
| `/rates` | GET | 100/minute | Get current mortgage rates |
| `/rates/historical` | GET | 50/minute | Get historical rates |
| `/rates/predict` | POST | 30/minute | Predict future rates |
| `/metrics` | GET | 60/minute | API metrics/statistics |

---

## 🔑 How Rate Limiting Works

**By Client IP Address:**
- Each client (identified by IP address) gets a separate rate limit bucket
- Rate limits reset every **60 seconds**
- Limits are counted per endpoint

**Example:**
- You can make **100 `/rates` requests per minute**
- You can make **30 `/decision` requests per minute**
- Each endpoint has its own counter

---

## ⚠️ What Happens When You Exceed the Limit

When you exceed the rate limit:

```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "retry_after": "60 seconds"
}
```

**Response Status:** `429 Too Many Requests`

**Headers included:**
- `Retry-After`: Seconds until you can make another request
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

---

## 💡 Best Practices

### ✅ DO:
- Cache results when possible
- Use batch endpoints for multiple users
- Spread requests across time (don't burst)
- Check `Retry-After` header before retrying
- Implement exponential backoff in retry logic

### ❌ DON'T:
- Send rapid-fire requests in a loop
- Make parallel requests from same IP
- Ignore 429 responses and retry immediately
- Use the API for load testing

---

## 🎯 Recommended Rate Limiting Strategy

### For Single-User Queries
```python
import time
import requests

def get_decision_with_backoff(user_data, prediction):
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:8000/decision",
                json={"user_data": user_data, "prediction": prediction}
            )
            
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", retry_delay))
                print(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                retry_delay *= 2  # Exponential backoff
                continue
            
            return response.json()
        
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(retry_delay)
    
    raise Exception("Failed after max retries")
```

### For Batch Processing
```python
import time

def process_batch_with_rate_limit(users, predictions):
    results = []
    batch_size = 50  # Process 50 users per batch
    delay = 10  # 10 seconds between batches (under 10/minute limit)
    
    for i in range(0, len(users), batch_size):
        batch_users = users[i:i+batch_size]
        batch_preds = predictions[i:i+batch_size]
        
        # Rate limit: max 10 batch requests per minute
        if i > 0:
            time.sleep(delay)
        
        response = requests.post(
            "http://localhost:8000/batch",
            json={"users": batch_users, "predictions": batch_preds}
        )
        
        results.extend(response.json()["results"])
    
    return results
```

### For Rate Queries
```python
# /rates endpoint: 100/minute = 1.67 req/sec
# Safe to call every 1-2 seconds without hitting limit

import time

while True:
    response = requests.get("http://localhost:8000/rates?state=CA")
    rates = response.json()
    
    print(f"30-year rate: {rates['rates']['30_year']}%")
    print(f"Remaining requests this minute: {response.headers.get('X-RateLimit-Remaining')}")
    
    time.sleep(2)  # Safe delay between requests
```

---

## 📈 Monitoring Your Usage

Check the `/metrics` endpoint to see current usage:

```bash
curl http://localhost:8000/metrics
```

Response:
```json
{
  "timestamp": "2026-04-08T20:30:00",
  "uptime_seconds": 3600,
  "total_requests": 1524,
  "rate_limit_status": {
    "requests_this_minute": 45,
    "requests_remaining": 55
  }
}
```

---

## 🔧 Configuring Rate Limits

Rate limits are defined in [src/api_server.py](src/api_server.py) using the `@limiter.limit()` decorator:

```python
@app.get("/rates")
@limiter.limit("100/minute")  # <-- Rate limit configuration
async def get_current_rates():
    ...
```

To change limits:
1. Edit `src/api_server.py`
2. Find the endpoint you want to change
3. Modify the limit string (e.g., `"100/minute"` → `"200/minute"`)
4. Restart the API server

### Common Limit Formats:
- `100/minute` - 100 requests per minute
- `60/hour` - 60 requests per hour
- `10/second` - 10 requests per second

---

## 🐳 Docker & Production

Rate limiting is **automatically enabled** in all deployment modes:

- **Local development:** Uses client IP (usually 127.0.0.1)
- **Docker:** Uses container IP
- **AWS:** Uses real client IPs (with proper proxy headers)

**For AWS behind a load balancer:**
```python
# The limiter automatically detects CloudFlare, AWS, etc.
limiter = Limiter(
    key_func=get_remote_address,  # Auto-detects real IP
    default_limits=["200/minute"]  # Fallback global limit
)
```

---

## 🚨 Troubleshooting

### "Rate limit exceeded" error on first request?
- Check if you're making multiple requests simultaneously
- Each endpoint has its own limit counter
- Waiting 60 seconds resets all counters

### Different IP addresses getting rate limited?
- This is expected - each IP has separate limits
- Within an organization/network, clients might share IPs

### Need higher limits?
- Edit `@limiter.limit()` decorators in [src/api_server.py](src/api_server.py)
- Or contact the API administrator
- Can set per-user/API-key limits (future feature)

---

## 📋 Summary

| Feature | Status |
|---------|--------|
| Rate limiting enabled | ✅ Yes |
| Per-IP tracking | ✅ Yes |
| Per-endpoint limits | ✅ Yes |
| Automatic reset | ✅ 60 seconds |
| Error response (429) | ✅ Yes |
| Retry headers | ✅ Yes |
| Metrics tracking | ✅ Yes |
| Configurable | ✅ Yes |

---

**Questions?** Check the [AWS_PARAMETER_STORE_DEPLOY.md](AWS_PARAMETER_STORE_DEPLOY.md) or [PRODUCTION_SECURITY_GUIDE.md](docs/PRODUCTION_SECURITY_GUIDE.md) for more details.
