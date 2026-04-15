# 🚀 Mortgage Rate Notifier - AWS Deployment Script
# Automated deployment to AWS ECS Fargate with Parameter Store integration

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("check", "credentials", "docker", "build-push", "deploy-ecs", "full")]
    [string]$Step = "full",
    
    [Parameter(Mandatory=$false)]
    [string]$AccountId = "105726692206",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$FredApiKey = "YOUR-FRED-API-KEY-HERE"
)

$ErrorActionPreference = "Stop"
$WarningPreference = "Continue"

# Colors for output
$Red = @{ ForegroundColor = 'Red' }
$Green = @{ ForegroundColor = 'Green' }
$Yellow = @{ ForegroundColor = 'Yellow' }
$Cyan = @{ ForegroundColor = 'Cyan' }

function Write-Status {
    param([string]$Message, [ValidateSet("info", "success", "warning", "error")]$Type = "info")
    
    switch ($Type) {
        "success" { Write-Host "✅ $Message" @Green }
        "warning" { Write-Host "⚠️  $Message" @Yellow }
        "error" { Write-Host "❌ $Message" @Red }
        default { Write-Host "ℹ️  $Message" @Cyan }
    }
}

function Check-Prerequisites {
    Write-Host "`n" 
    Write-Host "📋 Checking Prerequisites..." @Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    $missing = @()
    
    # Check AWS CLI
    try {
        $awsVersion = aws --version 2>&1
        Write-Status "AWS CLI: $awsVersion" "success"
    } catch {
        Write-Status "AWS CLI not found. Download from: https://aws.amazon.com/cli/" "error"
        $missing += "AWS CLI"
    }
    
    # Check Docker
    try {
        $dockerVersion = docker --version 2>&1
        Write-Status "Docker: $dockerVersion" "success"
    } catch {
        Write-Status "Docker not installed. Download from: https://www.docker.com/products/docker-desktop" "warning"
        $missing += "Docker"
    }
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Status "Python: $pythonVersion" "success"
    } catch {
        Write-Status "Python not found" "error"
        $missing += "Python"
    }
    
    # Check AWS credentials
    try {
        $identity = aws sts get-caller-identity --region $Region --output json | ConvertFrom-Json
        Write-Status "AWS Account: $($identity.Account)" "success"
        Write-Status "AWS User: $($identity.Arn)" "success"
    } catch {
        Write-Status "AWS credentials not configured. Run: aws configure" "warning"
        $missing += "AWS Credentials"
    }
    
    if ($missing.Count -gt 0) {
        Write-Host "`n⚠️  Missing components: $($missing -join ', ')" @Yellow
        return $false
    }
    
    Write-Status "All prerequisites OK!" "success"
    return $true
}

function Configure-Credentials {
    Write-Host "`n"
    Write-Host "🔐 Configuring AWS Credentials..." @Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    Write-Host "`nStep 1: Get your AWS credentials:"
    Write-Host "  1. Go to: https://console.aws.amazon.com/"
    Write-Host "  2. Click your profile → Security Credentials"
    Write-Host "  3. Find Access keys → Create New Access Key"
    Write-Host "  4. Save Access Key ID and Secret Access Key`n"
    
    Write-Host "Step 2: Run the following command and paste your credentials:"
    Write-Host "  aws configure`n" @Yellow
    
    $response = Read-Host "Press Enter when AWS CLI is configured, or type 'skip' to continue"
    
    if ($response -ne "skip") {
        # Verify credentials
        try {
            $identity = aws sts get-caller-identity --region $Region --output json | ConvertFrom-Json
            Write-Status "AWS configured successfully!" "success"
            Write-Status "Account: $($identity.Account)" "success"
            return $true
        } catch {
            Write-Status "Failed to verify AWS credentials" "error"
            return $false
        }
    }
    
    return $true
}

function Build-PushDocker {
    Write-Host "`n"
    Write-Host "🐳 Building and Pushing Docker Image..." @Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Create ECR repository
    Write-Status "Creating ECR repository..." "info"
    try {
        aws ecr create-repository `
            --repository-name mortgage-rate-notifier `
            --region $Region 2>&1 | Out-Null
        Write-Status "ECR repository created" "success"
    } catch {
        if ($_ -match "RepositoryAlreadyExistsException") {
            Write-Status "ECR repository already exists" "success"
        } else {
            Write-Status "Error creating ECR repository: $_" "error"
            return $false
        }
    }
    
    # Build Docker image
    Write-Status "Building Docker image (this may take 2-5 minutes)..." "info"
    docker build -f docker/Dockerfile.production -t mortgage-rate-notifier:latest . 2>&1 | Tee-Object -Variable buildOutput | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Status "Docker build failed" "error"
        return $false
    }
    Write-Status "Docker image built successfully" "success"
    
    # Login to ECR
    Write-Status "Logging into AWS ECR..." "info"
    $token = aws ecr get-login-password --region $Region
    docker login --username AWS --password $token "$AccountId.dkr.ecr.$Region.amazonaws.com" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Status "ECR login failed" "error"
        return $false
    }
    Write-Status "ECR login successful" "success"
    
    # Tag and push image
    Write-Status "Pushing image to ECR..." "info"
    $repoUri = "$AccountId.dkr.ecr.$Region.amazonaws.com/mortgage-rate-notifier"
    docker tag mortgage-rate-notifier:latest "$repoUri:latest" 2>&1 | Out-Null
    docker push "$repoUri:latest" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Status "Docker push failed" "error"
        return $false
    }
    Write-Status "Image pushed to ECR successfully" "success"
    Write-Status "Repository URI: $repoUri" "success"
    
    return $true
}

function Store-ApiKey {
    Write-Host "`n"
    Write-Host "🔑 Storing API Key in Parameter Store..." @Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    Write-Status "Storing FRED API Key..." "info"
    aws ssm put-parameter `
        --name "/mortgage-rate-notifier/FRED_API_KEY" `
        --value $FredApiKey `
        --type "SecureString" `
        --region $Region `
        --overwrite 2>&1 | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Status "Failed to store API key" "error"
        return $false
    }
    
    Write-Status "API key stored in Parameter Store" "success"
    
    # Verify
    Write-Status "Verifying..." "info"
    aws ssm get-parameter `
        --name "/mortgage-rate-notifier/FRED_API_KEY" `
        --with-decryption `
        --region $Region 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "API key verified successfully" "success"
        return $true
    }
    
    return $false
}

function Deploy-ECS {
    Write-Host "`n"
    Write-Host "☁️  Deploying to ECS Fargate..." @Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Create ECS cluster
    Write-Status "Creating ECS cluster..." "info"
    try {
        aws ecs create-cluster `
            --cluster-name mortgage-rate-notifier `
            --region $Region 2>&1 | Out-Null
        Write-Status "ECS cluster created" "success"
    } catch {
        if ($_ -match "ClusterAlreadyExistsException") {
            Write-Status "ECS cluster already exists" "success"
        } else {
            Write-Status "Error creating ECS cluster: $_" "error"
            return $false
        }
    }
    
    # Create CloudWatch log group
    Write-Status "Creating CloudWatch log group..." "info"
    try {
        aws logs create-log-group `
            --log-group-name /ecs/mortgage-rate-notifier `
            --region $Region 2>&1 | Out-Null
        Write-Status "Log group created" "success"
    } catch {
        if ($_ -match "ResourceAlreadyExistsException") {
            Write-Status "Log group already exists" "success"
        } else {
            Write-Status "Error creating log group: $_" "error"
        }
    }
    
    # Get repository URI
    $repoUri = "$AccountId.dkr.ecr.$Region.amazonaws.com/mortgage-rate-notifier:latest"
    
    Write-Status "Deployment setup complete!" "success"
    Write-Status "Cluster Name: mortgage-rate-notifier" "success"
    Write-Status "Region: $Region" "success"
    Write-Status "Image URI: $repoUri" "success"
    
    Write-Host "`n📖 Next Steps:"
    Write-Host "  1. Create ECS Service and Task Definition in AWS Console, OR"
    Write-Host "  2. Use CloudFormation template (coming soon)"
    Write-Host "  3. Configure Application Load Balancer for public access"
    Write-Host "  4. Test with: curl -X GET http://your-load-balancer:8000/health"
    
    return $true
}

function Show-Menu {
    Write-Host "`n🚀 Mortgage Rate Notifier - AWS Deployment" @Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n"
    Write-Host "Available steps:"
    Write-Host "  check       - Check prerequisites"
    Write-Host "  credentials - Configure AWS credentials"
    Write-Host "  docker      - Build and push Docker image"
    Write-Host "  deploy-ecs  - Deploy to ECS Fargate"
    Write-Host "  full        - Run all steps"
    Write-Host "`nUsage: .\deploy-aws.ps1 -Step <step-name>`n"
}

# Main execution
if ($Step -eq "check" -or $Step -eq "full") {
    if (-not (Check-Prerequisites)) {
        if ($Step -eq "check") { exit 1 }
        Write-Status "Some prerequisites missing. Continuing anyway..." "warning"
    }
}

if ($Step -eq "credentials" -or $Step -eq "full") {
    if (-not (Configure-Credentials)) {
        Write-Status "Failed to configure credentials" "error"
        exit 1
    }
}

if ($Step -eq "docker" -or $Step -eq "full") {
    if (-not (Build-PushDocker)) {
        Write-Status "Failed to build and push Docker image" "error"
        exit 1
    }
    
    if (-not (Store-ApiKey)) {
        Write-Status "Failed to store API key" "error"
        exit 1
    }
}

if ($Step -eq "deploy-ecs" -or $Step -eq "full") {
    if (-not (Deploy-ECS)) {
        Write-Status "Failed to deploy to ECS" "error"
        exit 1
    }
}

Write-Host "`n"
Write-Status "Deployment process completed successfully! 🎉" "success"
