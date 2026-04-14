# 🚀 AWS Lambda Deployment Guide - Mortgage Rate Notifier

Complete guide to deploy your Mortgage Rate Notifier to AWS Lambda (serverless).

**Status:** ✅ Ready to deploy  
**Cost:** ~$0-20/month  
**Setup time:** 15-30 minutes  
**Zero Docker required** ✅

---

## 📋 Prerequisites

- ✅ AWS Account (you have: `105726692206`)
- ✅ AWS CLI installed
- ✅ FRED API Key: `YOUR-FRED-API-KEY-HERE`
- ✅ OpenAI API Key
- ✅ CloudFormation knowledge (basic)

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────┐
│         Client Applications                 │
│      (Web, Mobile, API Calls)              │
└──────────────┬──────────────────────────────┘
               │ HTTPS
               ▼
┌─────────────────────────────────────────────┐
│      API Gateway (REST API)                 │
│  /decision  /batch  /health  /metrics       │
└──────────────┬──────────────────────────────┘
               │ Invoke
               ▼
┌─────────────────────────────────────────────┐
│    Lambda Function (Python 3.11)            │
│  ├─ rates_agent (FRED data)                │
│  ├─ rag_agent (knowledge base)             │
│  ├─ orchestrator (workflow)                │
│  └─ decision (RESTful handler)             │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴──────────┬──────────────┐
       ▼                  ▼              ▼
   ┌────────┐        ┌────────┐    ┌─────────────┐
   │ S3     │        │Parameter│   │SNS/SES      │
   │Docs    │        │Store    │   │Emails       │
   │(RAG)   │        │Secrets  │   │Notifications│
   └────────┘        └────────┘    └─────────────┘

CloudWatch: Logs, Metrics, Alarms
EventBridge: Keep-alive schedule (5-min warmup)
```

---

## 🏗️ Files Created for You

```
aws/
├── cloudformation-lambda.yaml    ← Full infrastructure
├── requirements-lambda.txt        ← Optimized dependencies
└── (existing files)

src/
├── lambda_handler.py             ← Lambda entry point
└── (existing files)

azure-pipelines.yml               ← CI/CD pipeline (ADO)
```

---

## 📋 Step 1: Prepare AWS Account

### 1.1 Create S3 Bucket for Lambda Code

```powershell
# Set variables
$ACCOUNT_ID = "105726692206"
$REGION = "us-east-1"

# Create S3 bucket for Lambda code
aws s3 mb s3://mortgage-rate-notifier-code-$ACCOUNT_ID --region $REGION

# Enable versioning
aws s3api put-bucket-versioning `
  --bucket mortgage-rate-notifier-code-$ACCOUNT_ID `
  --versioning-configuration Status=Enabled
```

### 1.2 Store Secrets in Parameter Store

```powershell
# Store FRED API Key
aws ssm put-parameter `
  --name "/mortgage-rate-notifier/FRED_API_KEY" `
  --value "YOUR-FRED-API-KEY-HERE" `
  --type "SecureString" `
  --region us-east-1 `
  --overwrite

# Store OpenAI API Key
aws ssm put-parameter `
  --name "/mortgage-rate-notifier/OPENAI_API_KEY" `
  --value "YOUR-OPENAI-KEY-HERE" `
  --type "SecureString" `
  --region us-east-1 `
  --overwrite

# Verify
aws ssm get-parameter `
  --name "/mortgage-rate-notifier/FRED_API_KEY" `
  --with-decryption `
  --region us-east-1
```

---

## 📦 Step 2: Build Deployment Package

### 2.1 Create Lambda Deployment Package

```powershell
# Navigate to project root
cd C:\Users\rames\projects\MortgageRateNotifier

# Create directory structure
mkdir lambda_package\src
mkdir lambda_package\agents

# Copy source files
Copy-Item -Path src\*.py -Destination lambda_package\src\
Copy-Item -Path agents\*.py -Destination lambda_package\agents\

# Install dependencies
pip install -r aws/requirements-lambda.txt -t lambda_package\

# Remove unnecessary files
Remove-Item -Path lambda_package\*.dist-info -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path lambda_package\*\__pycache__ -Recurse -Force -ErrorAction SilentlyContinue

# Create ZIP file
Compress-Archive -Path lambda_package\* -DestinationPath lambda-code.zip -Force

# Verify size (should be < 50MB)
(Get-Item lambda-code.zip).Length / 1MB
```

### 2.2 Create Lambda Layer for Dependencies

```powershell
# Create layer structure
mkdir python\lib\python3.11\site-packages

# Install dependencies
pip install -r aws/requirements-lambda.txt -t python\lib\python3.11\site-packages\

# Remove unnecessary files
Remove-Item -Path python\lib\python3.11\site-packages\*.dist-info -Recurse -Force -ErrorAction SilentlyContinue

# Create ZIP file
Compress-Archive -Path python -DestinationPath layer-dependencies.zip -Force
```

### 2.3 Create Layer for Financial Documents

```powershell
# Create layer structure for documents
mkdir python\data\financial_documents

# Copy financial documents
Copy-Item -Path data\financial_documents\* -Destination python\data\financial_documents\ -Force -ErrorAction SilentlyContinue

# Create ZIP file
Compress-Archive -Path python -DestinationPath layer-documents.zip -Force
```

---

## 📤 Step 3: Upload to S3

```powershell
$ACCOUNT_ID = "105726692206"
$REGION = "us-east-1"

# Upload Lambda code
aws s3 cp lambda-code.zip `
  s3://mortgage-rate-notifier-code-$ACCOUNT_ID/lambda-code-dev.zip

# Upload dependencies layer
aws s3 cp layer-dependencies.zip `
  s3://mortgage-rate-notifier-code-$ACCOUNT_ID/layer-dependencies-dev.zip

# Upload documents layer
aws s3 cp layer-documents.zip `
  s3://mortgage-rate-notifier-code-$ACCOUNT_ID/layer-documents-dev.zip
```

---

## 🚀 Step 4: Deploy CloudFormation Stack

### 4.1 Validate Template

```powershell
aws cloudformation validate-template `
  --template-body file://aws/cloudformation-lambda.yaml
```

### 4.2 Deploy Stack (Dev)

```powershell
$ACCOUNT_ID = "105726692206"
$REGION = "us-east-1"
$FRED_KEY = "YOUR-FRED-API-KEY-HERE"
$OPENAI_KEY = "sk-your-openai-key"

aws cloudformation deploy `
  --template-file aws/cloudformation-lambda.yaml `
  --stack-name mortgage-rate-notifier-dev `
  --parameter-overrides `
    EnvironmentName=dev `
    AccountId=$ACCOUNT_ID `
    FredApiKey=$FRED_KEY `
    OpenAiApiKey=$OPENAI_KEY `
    LambdaMemory=512 `
    LambdaTimeout=60 `
  --capabilities CAPABILITY_NAMED_IAM `
  --region $REGION
```

### 4.3 Get API Endpoint

```powershell
$ACCOUNT_ID = "105726692206"
$REGION = "us-east-1"

# Get outputs from CloudFormation
aws cloudformation describe-stacks `
  --stack-name mortgage-rate-notifier-dev `
  --query 'Stacks[0].Outputs' `
  --region $REGION

# Or get just the API endpoint
aws cloudformation describe-stacks `
  --stack-name mortgage-rate-notifier-dev `
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' `
  --output text `
  --region $REGION
```

---

## ✅ Step 5: Test the API

### 5.1 Health Check

```powershell
# Replace with your actual API endpoint
$API_ENDPOINT = "https://xxxxx.execute-api.us-east-1.amazonaws.com/dev"

# Test health endpoint
curl -X GET "$API_ENDPOINT/health" `
  -H "Content-Type: application/json"

# Expected response:
# {
#   "status": "healthy",
#   "service": "MortgageRateNotifier",
#   "version": "2.0.0-lambda",
#   ...
# }
```

### 5.2 Single Decision Request

```powershell
$API_ENDPOINT = "https://xxxxx.execute-api.us-east-1.amazonaws.com/dev"

$body = @{
    user_data = @{
        id = "USER-001"
        name = "John Doe"
        email = "john@example.com"
        current_rate = 4.5
        loan_term_years = 30
        monthly_payment = 1200
        closing_costs = 5500
        credit_score = 750
        loan_amount = 350000
        remaining_term = 240
    }
    prediction = @{
        predicted_direction = "DOWN"
        predicted_average_30d = 4.0
        min_rate = 3.9
        max_rate = 4.1
        confidence = 0.82
    }
    send_email = $false
} | ConvertTo-Json

curl -X POST "$API_ENDPOINT/decision" `
  -H "Content-Type: application/json" `
  -Body $body
```

### 5.3 Batch Processing Request

```powershell
$API_ENDPOINT = "https://xxxxx.execute-api.us-east-1.amazonaws.com/dev"

$batch = @{
    users = @(
        @{
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
        }
        # Add more users...
    )
    send_emails = $false
} | ConvertTo-Json

curl -X POST "$API_ENDPOINT/batch" `
  -H "Content-Type: application/json" `
  -Body $batch
```

---

## 📊 Performance & Costs

### Performance Metrics

| Metric | Value |
|--------|-------|
| Cold start | 1-3 seconds (first request) |
| Warm response | 50-100ms (subsequent requests) |
| Batch (100 users) | 5-10 seconds |
| Max concurrent | 1000 (auto-scales) |

### Cost Estimations

```
Level 1: 1K requests/day (30K/month)
├─ Lambda: $0.006/month
├─ API Gateway: $0.10/month
└─ Total: ~$0.10/month ✅

Level 2: 10K requests/day (300K/month)
├─ Lambda: $0.06/month
├─ API Gateway: $1.05/month
└─ Total: ~$1.11/month ✅

Level 3: 100K requests/day (3M/month)
├─ Lambda: $0.60/month
├─ API Gateway: $10.50/month
└─ Total: ~$11.10/month ✅
```

---

## 🔄 Production Deployment (Staging/Prod)

### Staging Deployment

```powershell
aws cloudformation deploy `
  --template-file aws/cloudformation-lambda.yaml `
  --stack-name mortgage-rate-notifier-staging `
  --parameter-overrides `
    EnvironmentName=staging `
    AccountId=$ACCOUNT_ID `
    FredApiKey=$FRED_KEY `
    OpenAiApiKey=$OPENAI_KEY `
    LambdaMemory=1024 `
    LambdaTimeout=120 `
  --capabilities CAPABILITY_NAMED_IAM `
  --region $REGION
```

### Production Deployment

```powershell
aws cloudformation deploy `
  --template-file aws/cloudformation-lambda.yaml `
  --stack-name mortgage-rate-notifier-prod `
  --parameter-overrides `
    EnvironmentName=prod `
    AccountId=$ACCOUNT_ID `
    FredApiKey=$FRED_KEY `
    OpenAiApiKey=$OPENAI_KEY `
    LambdaMemory=2048 `
    LambdaTimeout=300 `
  --capabilities CAPABILITY_NAMED_IAM `
  --region $REGION
```

---

## 🔍 Monitoring & Troubleshooting

### View Logs

```powershell
# Real-time logs
aws logs tail /aws/lambda/mortgage-rate-notifier-dev --follow

# Search for errors
aws logs filter-log-events `
  --log-group-name /aws/lambda/mortgage-rate-notifier-dev `
  --filter-pattern "ERROR"
```

### Check Metrics

```powershell
# Get function metrics
aws cloudwatch get-metric-statistics `
  --namespace AWS/Lambda `
  --metric-name Invocations `
  --dimensions Name=FunctionName,Value=mortgage-rate-notifier-dev `
  --start-time 2024-01-01T00:00:00Z `
  --end-time 2024-01-02T00:00:00Z `
  --period 3600 `
  --statistics Sum
```

### Update Lambda Code

```powershell
# Rebuild package
# ... (repeat steps 2.1-2.3)

# Upload new code
aws s3 cp lambda-code.zip s3://mortgage-rate-notifier-code-$ACCOUNT_ID/lambda-code-dev.zip

# Update Lambda function
aws lambda update-function-code `
  --function-name mortgage-rate-notifier-dev `
  --s3-bucket mortgage-rate-notifier-code-$ACCOUNT_ID `
  --s3-key lambda-code-dev.zip

# Wait for update to complete
aws lambda wait function-updated `
  --function-name mortgage-rate-notifier-dev
```

---

## 🚨 Troubleshooting

### Issue: "Permission denied" uploading to S3
**Solution:** Verify AWS credentials with `aws sts get-caller-identity`

### Issue: Lambda timeout (15+ seconds response)
**Solution:** Increase `LambdaTimeout` in CloudFormation template

### Issue: "Module not found" errors
**Solution:** Verify all dependencies are in `requirements-lambda.txt` and layers

### Issue: Cold starts > 3 seconds
**Solution:** Lambda keeps code warm with EventBridge warmup (every 5 min)

---

## 📚 Next Steps

1. ✅ Deploy to Dev environment (this guide)
2. ⏭️ Run comprehensive tests
3. ⏭️ Deploy to Staging
4. ⏭️ Performance testing & optimization
5. ⏭️ Deploy to Production
6. ⏭️ Set up monitoring & alerts

---

## 🔗 Useful Links

- AWS Lambda Console: https://console.aws.amazon.com/lambda/
- API Gateway Console: https://console.aws.amazon.com/apigateway/
- CloudFormation Console: https://console.aws.amazon.com/cloudformation/
- CloudWatch Logs: https://console.aws.amazon.com/logs/
- Parameter Store: https://console.aws.amazon.com/systems-manager/parameters/

---

## 💬 Questions?

- AWS Lambda FAQ: https://aws.amazon.com/lambda/faq/
- AWS Documentation: https://docs.aws.amazon.com/lambda/
- Support: contact AWS support

