# Publishing Guide - Mortgage Rate Notifier API

## Quick Publishing Options

| Method | Effort | Best For | Cost |
|--------|--------|----------|------|
| **AWS API Gateway Docs** | Low | Internal/Enterprise | Free |
| **OpenAPI/Swagger** | Medium | Technical users | Free |
| **API Key Portal** | Medium | Public access | $0-100/mo |
| **NPM/PyPI Package** | High | Developer SDKs | Free |
| **Public Website** | Medium | Marketing | $10-50/mo |
| **Developer Portal** | High | Full platform | $500+/mo |

---

## OPTION 1: AWS API Gateway Documentation (EASIEST) ✅

### Step 1: Generate OpenAPI Spec

```bash
aws apigateway get-export \
  --rest-api-id vors6gfapf \
  --stage-name dev \
  --export-type oas30 \
  --region us-east-1 \
  --output swagger.json
```

### Step 2: Create Documentation

```bash
# Install Swagger UI Docker image
docker run -d -p 8080:8080 \
  -e SWAGGER_JSON=/swagger.json \
  -v $(pwd)/swagger.json:/swagger.json \
  swaggerapi/swagger-ui
```

**Access at:** `http://localhost:8080`

---

## OPTION 2: AWS API Gateway Public Documentation

### Enable Documentation in AWS Console

```bash
# Via CLI
aws apigateway update-rest-api \
  --rest-api-id vors6gfapf \
  --patch-operations op=replace,path=/description,value="Mortgage Rate Notifier API" \
  --region us-east-1
```

**Then reference:** `https://docs.aws.amazon.com/apigateway/latest/developerguide/...`

---

## OPTION 3: Create OpenAPI/Swagger Documentation

Create file: `api-documentation.yaml`

```yaml
openapi: 3.0.0
info:
  title: Mortgage Rate Notifier API
  description: |
    # Mortgage Rate Notifier API
    
    Intelligent mortgage refinancing decision engine powered by AI and predictive analytics.
    
    ## Features
    - Real-time mortgage rate prediction
    - Personalized refinancing recommendations
    - Batch processing for multiple users
    - RAG-powered decision explanations
    - REST API with JSON payloads
  version: 1.0.0
  contact:
    name: Support
    email: support@mortgagenotifier.com
  license:
    name: Proprietary

servers:
  - url: https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev
    description: Production API

paths:
  /health:
    get:
      summary: Health Check
      description: Verify API is operational
      tags:
        - System
      responses:
        '200':
          description: Service is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "healthy"
                  service:
                    type: string
                    example: "Mortgage Rate Notifier"
                  version:
                    type: string
                    example: "1.0.0"
                  timestamp:
                    type: string
                    format: date-time

  /decision:
    post:
      summary: Analyze Mortgage Refinancing Decision
      description: |
        Process a single user's mortgage refinancing decision.
        
        Returns:
        - Recommendation (STRONGLY_RECOMMENDED, RECOMMENDED, MARGINAL, NOT_RECOMMENDED)
        - Estimated monthly savings
        - Breakeven period in months
        - Confidence score
      tags:
        - Decisions
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - user_data
                - prediction
              properties:
                user_data:
                  type: object
                  required:
                    - id
                    - name
                    - current_rate
                    - loan_term_years
                    - monthly_payment
                    - closing_costs
                    - credit_score
                  properties:
                    id:
                      type: string
                      description: Unique user identifier
                      example: "USER-001"
                    name:
                      type: string
                      example: "John Doe"
                    current_rate:
                      type: number
                      format: float
                      description: Current mortgage rate (%)
                      example: 4.5
                    loan_term_years:
                      type: integer
                      example: 30
                    monthly_payment:
                      type: number
                      format: float
                      description: Monthly mortgage payment ($)
                      example: 1200
                    closing_costs:
                      type: number
                      format: float
                      description: Estimated refinancing closing costs ($)
                      example: 5500
                    credit_score:
                      type: integer
                      example: 750
                prediction:
                  type: object
                  required:
                    - predicted_direction
                    - predicted_average_30d
                    - confidence
                  properties:
                    predicted_direction:
                      type: string
                      enum: ["DOWN", "UP", "STABLE"]
                      example: "DOWN"
                    predicted_average_30d:
                      type: number
                      format: float
                      description: Predicted average rate in 30 days (%)
                      example: 4.0
                    confidence:
                      type: number
                      format: float
                      minimum: 0
                      maximum: 1
                      example: 0.82
      responses:
        '200':
          description: Decision successfully processed
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  user_id:
                    type: string
                  decision:
                    type: object
                    properties:
                      recommendation:
                        type: string
                        enum:
                          - STRONGLY_RECOMMENDED
                          - RECOMMENDED
                          - MARGINAL
                          - NOT_RECOMMENDED
                      monthly_saving:
                        type: number
                        format: float
                      breakeven_months:
                        type: integer
                      confidence:
                        type: number
                        format: float
        '400':
          description: Invalid request parameters
        '500':
          description: Internal server error

  /batch:
    post:
      summary: Batch Process Multiple Users (Beta)
      description: Process up to 100 users in a single request
      tags:
        - Decisions
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: array
              maxItems: 100
              items:
                type: object
      responses:
        '200':
          description: Batch processing complete

  /metrics:
    get:
      summary: Get API Metrics
      description: Retrieve service performance metrics
      tags:
        - System
      responses:
        '200':
          description: Metrics retrieved successfully

components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      name: X-API-Key
      in: header
```

### View Documentation with Swagger UI:

```bash
docker run -d -p 8080:8080 \
  -e SWAGGER_JSON=/api-documentation.yaml \
  -v $(pwd)/api-documentation.yaml:/api-documentation.yaml \
  swaggerapi/swagger-ui
```

---

## OPTION 4: Create Client SDKs

### Python SDK Package

Create `mortgage_notifier_sdk/__init__.py`:

```python
"""Mortgage Rate Notifier SDK"""

import requests
import json
from typing import Dict, List, Optional

class MortgageNotifierClient:
    """Client for Mortgage Rate Notifier API"""
    
    def __init__(self, api_url: str = "https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev"):
        self.api_url = api_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict:
        """Check API health"""
        response = self.session.get(f"{self.api_url}/health")
        response.raise_for_status()
        return response.json()
    
    def analyze_decision(self, 
                        user_id: str,
                        name: str,
                        current_rate: float,
                        loan_term_years: int,
                        monthly_payment: float,
                        closing_costs: float,
                        credit_score: int,
                        predicted_direction: str,
                        predicted_average_30d: float,
                        confidence: float) -> Dict:
        """
        Analyze single mortgage decision
        
        Args:
            user_id: Unique user identifier
            name: User name
            current_rate: Current mortgage rate (%)
            loan_term_years: Loan term in years
            monthly_payment: Monthly payment ($)
            closing_costs: Closing costs ($)
            credit_score: Credit score (300-850)
            predicted_direction: "DOWN", "UP", or "STABLE"
            predicted_average_30d: Predicted avg rate in 30 days (%)
            confidence: Confidence level (0-1)
        
        Returns:
            Decision analysis with recommendation
        """
        payload = {
            "user_data": {
                "id": user_id,
                "name": name,
                "current_rate": current_rate,
                "loan_term_years": loan_term_years,
                "monthly_payment": monthly_payment,
                "closing_costs": closing_costs,
                "credit_score": credit_score
            },
            "prediction": {
                "predicted_direction": predicted_direction,
                "predicted_average_30d": predicted_average_30d,
                "confidence": confidence
            }
        }
        
        response = self.session.post(
            f"{self.api_url}/decision",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def batch_analyze(self, users: List[Dict]) -> Dict:
        """Process multiple users at once"""
        response = self.session.post(
            f"{self.api_url}/batch",
            json=users
        )
        response.raise_for_status()
        return response.json()
    
    def get_metrics(self) -> Dict:
        """Get API metrics"""
        response = self.session.get(f"{self.api_url}/metrics")
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == "__main__":
    client = MortgageNotifierClient()
    
    # Check health
    print(client.health_check())
    
    # Analyze decision
    result = client.analyze_decision(
        user_id="USER-001",
        name="John Doe",
        current_rate=4.5,
        loan_term_years=30,
        monthly_payment=1200,
        closing_costs=5500,
        credit_score=750,
        predicted_direction="DOWN",
        predicted_average_30d=4.0,
        confidence=0.82
    )
    print(result)
```

### Publish to PyPI

```bash
# 1. Create setup.py
cat > setup.py << 'EOF'
from setuptools import setup

setup(
    name="mortgage-notifier-sdk",
    version="1.0.0",
    author="Your Company",
    author_email="support@mortgagenotifier.com",
    description="SDK for Mortgage Rate Notifier API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mortgage-notifier-sdk",
    packages=["mortgage_notifier_sdk"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "requests>=2.28.0",
    ],
)
EOF

# 2. Install build tools
pip install build twine

# 3. Build package
python -m build

# 4. Upload to PyPI (requires account)
twine upload dist/*
```

### Users can then install it:

```bash
pip install mortgage-notifier-sdk
```

---

## OPTION 5: Create Developer Portal & Website

### Use AWS Amplify

```bash
# 1. Initialize Amplify app
amplify init

# 2. Add API documentation hosting
amplify add api

# 3. Deploy
amplify publish
```

### Or use ReadTheDocs

```bash
# 1. Create docs/conf.py
# 2. Add your API docs in Markdown
# 3. Connect GitHub repo to ReadTheDocs
# 4. Auto-deploy on git push
```

---

## OPTION 6: Docker Image for Easy Deployment

### Create `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy Lambda handler
COPY src/ src/
COPY agents/ agents/
COPY models/ models/
COPY requirements.txt .

RUN pip install -r requirements.txt

# Expose port
EXPOSE 8000

# Run with uvicorn (for local testing)
CMD ["uvicorn", "src.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and Push to Docker Hub

```bash
# 1. Build image
docker build -t yourusername/mortgage-notifier:latest .

# 2. Push to Docker Hub
docker push yourusername/mortgage-notifier:latest

# 3. Users can run it
docker run -p 8000:8000 yourusername/mortgage-notifier:latest
```

---

## OPTION 7: GitHub + GitHub Pages (RECOMMENDED)

### Create GitHub Repository

```bash
# 1. Create repo structure
mkdir mortgage-notifier-public
cd mortgage-notifier-public

# 2. Initialize git
git init
git add .
git commit -m "Initial commit"
git branch -M main

# 3. Push to GitHub
git push -u origin main
```

### Create `README.md`

```markdown
# Mortgage Rate Notifier API

Intelligent mortgage refinancing decision engine.

## Quick Start

### API Endpoint
```
https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev
```

### Health Check
```bash
curl https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev/health
```

### Using Python SDK
```python
from mortgage_notifier_sdk import MortgageNotifierClient

client = MortgageNotifierClient()
result = client.analyze_decision(...)
```

## Documentation
- [API Documentation](./docs/API.md)
- [Getting Started](./docs/GETTING_STARTED.md)
- [Examples](./docs/EXAMPLES.md)

## Support
Email: support@mortgagenotifier.com
```

### Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Select `main` branch, `/docs` folder
3. GitHub auto-publishes your docs

**Result:** `https://yourusername.github.io/mortgage-notifier-public`

---

## OPTION 8: Create NPM Package (For JavaScript/Node.js)

Create `mortgage-notifier-js/`:

```javascript
// index.js
class MortgageNotifierClient {
  constructor(apiUrl = 'https://vors6gfapf.execute-api.us-east-1.amazonaws.com/dev') {
    this.apiUrl = apiUrl;
  }

  async health() {
    return fetch(`${this.apiUrl}/health`).then(r => r.json());
  }

  async analyzeDecision(userData, prediction) {
    return fetch(`${this.apiUrl}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_data: userData, prediction })
    }).then(r => r.json());
  }
}

module.exports = MortgageNotifierClient;
```

### Publish to NPM

```bash
# 1. Create package.json
npm init

# 2. Login to NPM
npm login

# 3. Publish
npm publish
```

**Users install with:** `npm install mortgage-notifier-sdk`

---

## RECOMMENDED PUBLISHING STRATEGY (My Recommendation) 🎯

### Phase 1: IMMEDIATE (This Week)
- ✅ Create OpenAPI/Swagger documentation
- ✅ Publish to GitHub (README + docs)
- ✅ Create Python SDK
- ✅ Host on GitHub Pages

**Cost:** Free  
**Time:** 2-4 hours

### Phase 2: SHORT-TERM (Next Month)
- Publish Python SDK to PyPI
- Create npm package
- Create Docker image
- Set up CI/CD with GitHub Actions

**Cost:** Free  
**Time:** 4-8 hours

### Phase 3: LONG-TERM (Future)
- Create developer portal
- Add API key management
- Add usage analytics
- Create commercial tier

**Cost:** $100-500/month  
**Time:** 20+ hours

---

## PUBLISHING CHECKLIST

- [ ] API documentation (OpenAPI/Swagger)
- [ ] GitHub repository with README
- [ ] Example code snippets
- [ ] Client library (Python SDK)
- [ ] GitHub Pages documentation site
- [ ] API Testing guide
- [ ] Rate calculation documentation
- [ ] Error codes and troubleshooting
- [ ] Support email/contact
- [ ] License file (MIT/Apache)
- [ ] Contributing guidelines
- [ ] Changelog/release notes
- [ ] Performance SLA documentation
- [ ] Data privacy/security info

---

## Example Publishing URLs

| Resource | URL |
|----------|-----|
| GitHub Repo | `github.com/yourname/mortgage-notifier` |
| GitHub Pages Docs | `yourname.github.io/mortgage-notifier` |
| Python Package | `pypi.org/project/mortgage-notifier-sdk` |
| NPM Package | `npmjs.com/package/mortgage-notifier-sdk` |
| Docker Image | `docker.io/yourname/mortgage-notifier` |
| API Docs | `yourname.github.io/mortgage-notifier/api` |

---

## Next Steps

1. **Create GitHub Repository:** 5 minutes
2. **Write API Documentation:** 30 minutes
3. **Create Python SDK:** 1 hour
4. **Setup GitHub Pages:** 15 minutes
5. **Total:** ~2 hours → **PUBLISHED!**

See files already created:
- `API_TESTING_GUIDE.md` - Testing documentation
- `RATE_CALCULATION_EXPLAINED.md` - How it works
- `AWS_LAMBDA_DEPLOYMENT_LIVE.md` - Deployment info

These are already perfect for publishing! 🚀
