# Testing Mortgage Rate Notifier API - Decision Endpoint

## Quick Reference

**Endpoint:** `POST https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/decision`

**Base URL:** `https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev`

---

## 1. Test with cURL (Linux/macOS/Windows)

### Basic Health Check First
```bash
curl -X GET "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/health"
```

### Test Decision Endpoint
```bash
curl -X POST "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/decision" \
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

### Pretty Print Response
```bash
curl -X POST "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/decision" \
  -H "Content-Type: application/json" \
  -d '{...}' | jq '.'
```

---

## 2. Test with PowerShell (Windows)

### Health Check
```powershell
$healthUrl = "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/health"
Invoke-RestMethod -Uri $healthUrl -Method Get | ConvertTo-Json | Write-Host
```

### Decision Endpoint - Basic Test
```powershell
$url = "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/decision"

$body = @{
    user_data = @{
        id = "USER-001"
        name = "John Doe"
        current_rate = 4.5
        loan_term_years = 30
        monthly_payment = 1200
        closing_costs = 5500
        credit_score = 750
    }
    prediction = @{
        predicted_direction = "DOWN"
        predicted_average_30d = 4.0
        confidence = 0.82
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json"
$response | ConvertTo-Json | Write-Host
```

### Decision Endpoint - Detailed Test with Error Handling
```powershell
$url = "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/decision"

$body = @{
    user_data = @{
        id = "USER-002"
        name = "Jane Smith"
        current_rate = 3.8
        loan_term_years = 15
        monthly_payment = 1500
        closing_costs = 6000
        credit_score = 780
    }
    prediction = @{
        predicted_direction = "STABLE"
        predicted_average_30d = 3.7
        confidence = 0.75
    }
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $url `
        -Method Post `
        -Body $body `
        -ContentType "application/json" `
        -TimeoutSec 30
    
    Write-Host "Success:" -ForegroundColor Green
    $response | ConvertTo-Json | Write-Host
} catch {
    Write-Host "Error:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    if ($_.Exception.Response) {
        Write-Host "Status Code:" $_.Exception.Response.StatusCode.value__
    }
}
```

### Batch Test Multiple Decisions
```powershell
$url = "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/decision"

$testCases = @(
    @{
        name = "John - Rates Going Down"
        rate = 4.5
        direction = "DOWN"
        avg_rate = 4.0
    },
    @{
        name = "Jane - Rates Stable"
        rate = 3.8
        direction = "STABLE"
        avg_rate = 3.7
    },
    @{
        name = "Bob - Rates Going Up"
        rate = 3.5
        direction = "UP"
        avg_rate = 4.2
    }
)

foreach ($test in $testCases) {
    Write-Host "`n=== Testing: $($test.name) ===" -ForegroundColor Cyan
    
    $body = @{
        user_data = @{
            id = "USER-$(Get-Random)"
            name = $test.name
            current_rate = $test.rate
            loan_term_years = 30
            monthly_payment = 1200
            closing_costs = 5500
            credit_score = 750
        }
        prediction = @{
            predicted_direction = $test.direction
            predicted_average_30d = $test.avg_rate
            confidence = 0.82
        }
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json"
        Write-Host "Result: Success" -ForegroundColor Green
        Write-Host $response
    } catch {
        Write-Host "Result: Failed" -ForegroundColor Red
        Write-Host $_.Exception.Message
    }
}
```

---

## 3. Test with Python

### Simple Test
```python
import requests
import json

url = "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/decision"

payload = {
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

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers, timeout=10)

print(f"Status Code: {response.status_code}")
print(f"Response:\n{json.dumps(response.json(), indent=2)}")
```

### Advanced Test with Error Handling
```python
import requests
import json
from datetime import datetime

class APITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_health(self):
        """Test health endpoint"""
        url = f"{self.base_url}/health"
        try:
            response = self.session.get(url, timeout=10)
            print(f"✓ Health Check: {response.status_code}")
            print(json.dumps(response.json(), indent=2))
            return response.status_code == 200
        except Exception as e:
            print(f"✗ Health Check Failed: {e}")
            return False
    
    def test_decision(self, user_data, prediction):
        """Test decision endpoint"""
        url = f"{self.base_url}/decision"
        payload = {
            "user_data": user_data,
            "prediction": prediction
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            print(f"✓ Decision: {response.status_code}")
            print(json.dumps(response.json(), indent=2))
            return response.status_code == 200
        except Exception as e:
            print(f"✗ Decision Failed: {e}")
            return False
    
    def test_metrics(self):
        """Test metrics endpoint"""
        url = f"{self.base_url}/metrics"
        try:
            response = self.session.get(url, timeout=10)
            print(f"✓ Metrics: {response.status_code}")
            print(json.dumps(response.json(), indent=2))
            return response.status_code == 200
        except Exception as e:
            print(f"✗ Metrics Failed: {e}")
            return False

# Usage
if __name__ == "__main__":
    base_url = "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev"
    tester = APITester(base_url)
    
    print("=" * 60)
    print("Testing Mortgage Rate Notifier API")
    print("=" * 60)
    
    # Test 1: Health
    print("\n1. Testing Health Endpoint...")
    tester.test_health()
    
    # Test 2: Decision
    print("\n2. Testing Decision Endpoint...")
    user_data = {
        "id": "USER-001",
        "name": "John Doe",
        "current_rate": 4.5,
        "loan_term_years": 30,
        "monthly_payment": 1200,
        "closing_costs": 5500,
        "credit_score": 750
    }
    prediction = {
        "predicted_direction": "DOWN",
        "predicted_average_30d": 4.0,
        "confidence": 0.82
    }
    tester.test_decision(user_data, prediction)
    
    # Test 3: Metrics
    print("\n3. Testing Metrics Endpoint...")
    tester.test_metrics()
```

---

## 4. Test with Postman

### Import to Postman
1. Open Postman
2. Click **Import**
3. Paste this JSON:

```json
{
  "info": {
    "name": "Mortgage Rate Notifier",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": {
          "raw": "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/health",
          "protocol": "https",
          "host": ["vors6gfapf", "execute-api", "us-east-1", "amazonaws", "com"],
          "path": ["dev", "health"]
        }
      }
    },
    {
      "name": "Decision - Rates Going Down",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"user_data\": {\n    \"id\": \"USER-001\",\n    \"name\": \"John Doe\",\n    \"current_rate\": 4.5,\n    \"loan_term_years\": 30,\n    \"monthly_payment\": 1200,\n    \"closing_costs\": 5500,\n    \"credit_score\": 750\n  },\n  \"prediction\": {\n    \"predicted_direction\": \"DOWN\",\n    \"predicted_average_30d\": 4.0,\n    \"confidence\": 0.82\n  }\n}"
        },
        "url": {
          "raw": "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/decision",
          "protocol": "https",
          "host": ["vors6gfapf", "execute-api", "us-east-1", "amazonaws", "com"],
          "path": ["dev", "decision"]
        }
      }
    }
  ]
}
```

---

## 5. Sample Request/Response Payloads

### Request Example 1: User with Good Credit
```json
{
  "user_data": {
    "id": "USER-001",
    "name": "Alice Johnson",
    "current_rate": 5.2,
    "loan_term_years": 30,
    "monthly_payment": 1350,
    "closing_costs": 6500,
    "credit_score": 780
  },
  "prediction": {
    "predicted_direction": "DOWN",
    "predicted_average_30d": 4.8,
    "confidence": 0.88
  }
}
```

### Request Example 2: User with Fair Credit
```json
{
  "user_data": {
    "id": "USER-002",
    "name": "Bob Smith",
    "current_rate": 6.0,
    "loan_term_years": 20,
    "monthly_payment": 1600,
    "closing_costs": 7200,
    "credit_score": 650
  },
  "prediction": {
    "predicted_direction": "STABLE",
    "predicted_average_30d": 5.95,
    "confidence": 0.70
  }
}
```

### Request Example 3: User Considering Early Payoff
```json
{
  "user_data": {
    "id": "USER-003",
    "name": "Carol White",
    "current_rate": 3.5,
    "loan_term_years": 15,
    "monthly_payment": 2000,
    "closing_costs": 5000,
    "credit_score": 800
  },
  "prediction": {
    "predicted_direction": "UP",
    "predicted_average_30d": 4.2,
    "confidence": 0.75
  }
}
```

### Expected Response
```json
{
  "success": true,
  "request_id": "abc123def456",
  "user_id": "USER-001",
  "decision": {
    "recommendation": "CONSIDER_REFINANCING",
    "confidence_score": 0.82,
    "estimated_savings": 2500,
    "breakeven_months": 18
  },
  "timestamp": "2026-04-14T10:30:45.123Z"
}
```

---

## 6. Troubleshooting

### Common Errors

**Error: 400 Bad Request**
```
Check:
- JSON format is valid (use jq or online validator)
- Required fields are present
- Data types match (numbers, strings, etc.)
```

**Error: 500 Internal Server Error**
```
Check CloudWatch logs:
aws logs tail /aws/lambda/mortgage-rate-notifier-dev --follow --region us-east-1
```

**Error: Timeout**
```
The API might be slow on first request (cold start).
Wait a moment and retry.
```

**Error: Connection Refused**
```
- Verify the URL is correct
- Check AWS Lambda function status
- Verify API Gateway deployment
```

---

## 7. Load Testing

### Using Apache Bench
```bash
ab -n 100 -c 10 -p payload.json -T application/json \
  https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/health
```

### Using Python (Parallel Requests)
```python
import concurrent.futures
import requests
import time

def test_api(test_num):
    url = "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/decision"
    payload = {
        "user_data": {
            "id": f"USER-{test_num}",
            "name": f"Test User {test_num}",
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
    
    start = time.time()
    response = requests.post(url, json=payload, timeout=30)
    duration = time.time() - start
    
    return {
        "test_num": test_num,
        "status": response.status_code,
        "duration_ms": duration * 1000
    }

# Run 50 concurrent tests
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(test_api, range(50)))

# Print results
for result in results:
    print(f"Test {result['test_num']}: {result['status']} - {result['duration_ms']:.2f}ms")
```

---

## 8. Monitoring & Logging

### View Lambda Logs
```bash
aws logs tail /aws/lambda/mortgage-rate-notifier-dev --follow --region us-east-1
```

### Check API Metrics
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=mortgage-rate-notifier-dev \
  --start-time 2026-04-14T00:00:00Z \
  --end-time 2026-04-14T23:59:59Z \
  --period 3600 \
  --statistics Sum \
  --region us-east-1
```

---

## Summary: Quick Test Commands

```bash
# 1. Health Check (Test API is up)
curl -X GET "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/health"

# 2. Simple Decision Test
curl -X POST "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/decision" \
  -H "Content-Type: application/json" \
  -d '{"user_data":{"id":"U1","name":"Test","current_rate":4.5,"loan_term_years":30,"monthly_payment":1200,"closing_costs":5500,"credit_score":750},"prediction":{"predicted_direction":"DOWN","predicted_average_30d":4.0,"confidence":0.82}}'

# 3. Batch Test (Multiple Users)
curl -X POST "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/batch" \
  -H "Content-Type: application/json" \
  -d '[{...}, {...}]'

# 4. Get Metrics
curl -X GET "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/metrics"
```

---

**Need help?** Check AWS CloudWatch logs or contact your AWS administrator.
