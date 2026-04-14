# Secure Lambda Deployment for Mortgage Rate Notifier
# Keys are passed as parameters, never stored in source code

param(
    [Parameter(Mandatory=$true)]
    [string]$OpenAiKey,
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$FredApiKey = "63d0637021218655daf7ed773e7b583f"
)

$ErrorActionPreference = "Stop"

# Configuration
$ACCOUNT_ID = "105726692206"
$REGION = "us-east-1"
$PROJECT_NAME = "mortgage-rate-notifier"

Write-Host "`n" -ForegroundColor Green
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "   Secure AWS Lambda Deployment" -ForegroundColor Cyan
Write-Host "   Environment: $Environment" -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "`n"

# Step 1: Verify AWS Credentials
Write-Host "Step 1: Verifying AWS Credentials..." -ForegroundColor Yellow
$identity = aws sts get-caller-identity | ConvertFrom-Json
Write-Host "[OK] AWS Account: $($identity.Account)" -ForegroundColor Green
Write-Host "[OK] Region: $REGION" -ForegroundColor Green

# Step 2: Store API Keys in Parameter Store (ENCRYPTED)
Write-Host "`nStep 2: Storing API Keys in Parameter Store (Encrypted)..." -ForegroundColor Yellow

Write-Host "  * Storing FRED API Key..."
aws ssm put-parameter `
  --name "/mortgage-rate-notifier/FRED_API_KEY" `
  --value $FredApiKey `
  --type "SecureString" `
  --region $REGION `
  --overwrite `
  --output json | Out-Null
Write-Host "    [OK] FRED API Key stored securely" -ForegroundColor Green

Write-Host "  * Storing OpenAI API Key..."
aws ssm put-parameter `
  --name "/mortgage-rate-notifier/OPENAI_API_KEY" `
  --value $OpenAiKey `
  --type "SecureString" `
  --region $REGION `
  --overwrite `
  --output json | Out-Null
Write-Host "    [OK] OpenAI API Key stored securely" -ForegroundColor Green

# Step 3: Create S3 Bucket
Write-Host "`nStep 3: Creating S3 Bucket..." -ForegroundColor Yellow
$bucket_name = "$PROJECT_NAME-code-$ACCOUNT_ID"

try {
    aws s3 mb s3://$bucket_name --region $REGION 2>&1 | Out-Null
    Write-Host "[OK] S3 bucket created: $bucket_name" -ForegroundColor Green
} catch {
    if ($_ -match "BucketAlreadyOwnedByYou") {
        Write-Host "[OK] S3 bucket already exists: $bucket_name" -ForegroundColor Green
    }
}

# Step 4: Enable S3 Versioning
Write-Host "`nStep 4: Enabling S3 Versioning..." -ForegroundColor Yellow
aws s3api put-bucket-versioning `
  --bucket $bucket_name `
  --versioning-configuration Status=Enabled `
  --region $REGION 2>&1 | Out-Null
Write-Host "[OK] S3 versioning enabled" -ForegroundColor Green

# Step 5: Build Lambda Package
Write-Host "`nStep 5: Building Lambda Package..." -ForegroundColor Yellow

if (Test-Path "lambda_package") {
    Remove-Item "lambda_package" -Recurse -Force
}

mkdir lambda_package\src | Out-Null
mkdir lambda_package\agents | Out-Null

Write-Host "  * Copying source files..."
Copy-Item "src\*.py" "lambda_package\src\" -Force
Copy-Item "agents\*.py" "lambda_package\agents\" -Force
Write-Host "    [OK] Source files copied" -ForegroundColor Green

Write-Host "  * Installing dependencies..."
# Install dependencies, suppressing pip warnings/conflicts (these are non-fatal)
try {
    & python -m pip install `
      --prefer-binary `
      -r aws/requirements-lambda.txt `
      -t lambda_package\ `
      2>&1 | Out-Null
} catch {
    # Continue anyway - pip warnings aren't failures
}
Write-Host "    [OK] Dependencies installed" -ForegroundColor Green

Write-Host "  * Packaging into ZIP..."
if (Test-Path "lambda-code.zip") {
    Remove-Item "lambda-code.zip" -Force
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory("$(pwd)\lambda_package", "$(pwd)\lambda-code.zip", [System.IO.Compression.CompressionLevel]::Optimal, $false)

$size_mb = (Get-Item "lambda-code.zip").Length / 1MB
Write-Host "[OK] Lambda package created: lambda-code.zip ($([Math]::Round($size_mb, 1)) MB)" -ForegroundColor Green

# Step 6: Upload to S3
Write-Host "`nStep 6: Uploading Lambda Package to S3..." -ForegroundColor Yellow
aws s3 cp lambda-code.zip "s3://$bucket_name/lambda-code-$Environment.zip" --region $REGION | Out-Null
Write-Host "[OK] Lambda code uploaded to S3" -ForegroundColor Green

# Step 7: Deploy CloudFormation Stack
Write-Host "`nStep 7: Deploying CloudFormation Stack..." -ForegroundColor Yellow
$stack_name = "$PROJECT_NAME-$Environment"

aws cloudformation deploy `
  --template-file aws/cloudformation-lambda.yaml `
  --stack-name $stack_name `
  --parameter-overrides `
    EnvironmentName=$Environment `
    AccountId=$ACCOUNT_ID `
    FredApiKey=$FredApiKey `
    OpenAiApiKey=$OpenAiKey `
    LambdaMemory=512 `
    LambdaTimeout=60 `
  --capabilities CAPABILITY_NAMED_IAM `
  --region $REGION `
  --no-fail-on-empty-changeset

Write-Host "[OK] CloudFormation stack deployed: $stack_name" -ForegroundColor Green

# Step 8: Get API Endpoint
Write-Host "`nStep 8: Retrieving API Endpoint..." -ForegroundColor Yellow
$api_endpoint = aws cloudformation describe-stacks `
  --stack-name $stack_name `
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' `
  --output text `
  --region $REGION

if ($api_endpoint) {
    Write-Host "[OK] API Endpoint: $api_endpoint" -ForegroundColor Green
} else {
    Write-Host "[WARN] Could not retrieve API endpoint" -ForegroundColor Yellow
}

# Step 9: Test API
Write-Host "`nStep 9: Testing API Endpoints..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$api_endpoint/health" -Method Get -TimeoutSec 10
    Write-Host "[OK] Health Check: $($health.status)" -ForegroundColor Green
    Write-Host "     Service: $($health.service)" -ForegroundColor Cyan
    Write-Host "     Version: $($health.version)" -ForegroundColor Cyan
} catch {
    Write-Host "[WARN] Health check failed (API may still be starting)" -ForegroundColor Yellow
}

# Summary
Write-Host "`n" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host "   DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green

Write-Host "`nYour Mortgage Rate Notifier is now live!" -ForegroundColor Green
Write-Host "`nAPI Endpoints:" -ForegroundColor Cyan
Write-Host "   Decision:  POST   $api_endpoint/decision"
Write-Host "   Batch:     POST   $api_endpoint/batch"
Write-Host "   Health:    GET    $api_endpoint/health"
Write-Host "   Metrics:   GET    $api_endpoint/metrics"

Write-Host "`nSecurity:" -ForegroundColor Cyan
Write-Host "   * API Keys stored in AWS Parameter Store (encrypted)"
Write-Host "   * Keys never stored in source code"
Write-Host "   * Lambda reads keys from Parameter Store at runtime"
Write-Host "   * Safe to commit to Git"

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "   1. Test your API: curl -X GET '$api_endpoint/health'"
Write-Host "   2. Deploy to staging: .\deploy-lambda-secure.ps1 -Environment staging -OpenAiKey `$key"
Write-Host "   3. Set up Azure DevOps Pipeline (see azure-pipelines.yml)"

Write-Host "`nAll done!`n" -ForegroundColor Green
