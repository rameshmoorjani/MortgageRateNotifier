# 🚀 AWS Deployment Guide - Step by Step

Complete guide to deploy Mortgage Rate Notifier to AWS with ECS Fargate (simplest option).

**Estimated Time:** 30-45 minutes  
**Cost:** $4-6/month (includes free tier)

---

## 📋 Prerequisites Checklist

Before starting, make sure you have:

- [ ] AWS Account created (free tier available)
- [ ] AWS CLI installed (`aws --version` works)
- [ ] Docker installed locally
- [ ] FRED API key: `YOUR-FRED-API-KEY-HERE`
- [ ] Your AWS credentials (`Access Key ID` and `Secret Access Key`)

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Get Your AWS Credentials

1. Go to: https://console.aws.amazon.com/
2. Login with your AWS account
3. Click your profile → **Security Credentials**
4. Find **Access keys**
5. Click **Create New Access Key**
6. **Save these securely** - you'll need them!
   - Access Key ID: `AKIA...`
   - Secret Access Key: `wJal...`

### Step 2: Configure AWS CLI

```powershell
# Configure AWS with your credentials
python -m aws configure

# When prompted, enter:
# AWS Access Key ID: AKIA... (paste from above)
# AWS Secret Access Key: wJal... (paste from above)
# Default region: us-east-1
# Default output format: json
```

### Step 3: Verify Configuration

```powershell
# Test that your credentials work
python -m aws sts get-caller-identity
```

Expected output:
```json
{
  "UserId": "AIDAI...",
  "Account": "123456789012",
  "Arn": "arn:aws:iam::123456789012:root"
}
```

If you see this, you're ready! ✅

---

## 🐳 Step 4: Build and Push Docker Image

### Create ECR Repository

```powershell
# Create a Docker image repository on AWS
python -m aws ecr create-repository `
  --repository-name mortgage-rate-notifier `
  --region us-east-1
```

**Save the output** - you'll need the `repositoryUri`

### Build Docker Image

```powershell
# Build the Docker image locally
docker build -f docker/Dockerfile.production -t mortgage-rate-notifier:latest .

# Verify it built successfully
docker images | findstr mortgage-rate-notifier
```

### Push to AWS ECR

```powershell
# Get your AWS Account ID
$ACCOUNT_ID = python -m aws sts get-caller-identity --query Account --output text

# Login to ECR
$token = python -m aws ecr get-login-password --region us-east-1
docker login --username AWS --password $token "$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com"

# Tag the image for ECR
$REPO_URI = "$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/mortgage-rate-notifier"
docker tag mortgage-rate-notifier:latest "$REPO_URI:latest"

# Push to ECR
docker push "$REPO_URI:latest"

# Verify push succeeded
python -m aws ecr describe-images --repository-name mortgage-rate-notifier --region us-east-1
```

---

## ☁️ Step 5: Deploy to AWS ECS Fargate

### Create ECS Cluster

```powershell
# Create a cluster to run your application
python -m aws ecs create-cluster `
  --cluster-name mortgage-rate-notifier `
  --region us-east-1
```

### Create CloudWatch Log Group

```powershell
# Create logs for your application
python -m aws logs create-log-group `
  --log-group-name /ecs/mortgage-rate-notifier `
  --region us-east-1

# Set retention to 30 days (optional)
python -m aws logs put-retention-policy `
  --log-group-name /ecs/mortgage-rate-notifier `
  --retention-in-days 30 `
  --region us-east-1
```

### Store API Key in Parameter Store

```powershell
# Store your FRED API key securely
python -m aws ssm put-parameter `
  --name "/mortgage-rate-notifier/FRED_API_KEY" `
  --value "YOUR-FRED-API-KEY-HERE" `
  --type "SecureString" `
  --region us-east-1

# Verify it was stored
python -m aws ssm get-parameter `
  --name "/mortgage-rate-notifier/FRED_API_KEY" `
  --with-decryption `
  --region us-east-1
```

### Create IAM Role for ECS Task

```powershell
# Create trust policy for ECS
@{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Principal = @{
                Service = "ecs-tasks.amazonaws.com"
            }
            Action = "sts:AssumeRole"
        }
    )
} | ConvertTo-Json -Depth 2 | Out-File ecsTaskRole.json

# Create the role
python -m aws iam create-role `
  --role-name ecsTaskExecutionRole-mortgage `
  --assume-role-policy-document file://ecsTaskRole.json `
  --region us-east-1

# Attach required policies
python -m aws iam attach-role-policy `
  --role-name ecsTaskExecutionRole-mortgage `
  --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy" `
  --region us-east-1

# Create policy for Parameter Store access
@{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @(
                "ssm:GetParameter"
                "ssm:GetParameters"
            )
            Resource = "arn:aws:ssm:us-east-1:*:parameter/mortgage-rate-notifier/*"
        }
        @{
            Effect = "Allow"
            Action = @(
                "kms:Decrypt"
            )
            Resource = "*"
        }
    )
} | ConvertTo-Json -Depth 2 | Out-File parameterPolicy.json

# Attach the policy
python -m aws iam put-role-policy `
  --role-name ecsTaskExecutionRole-mortgage `
  --policy-name AllowParameterStore `
  --policy-document file://parameterPolicy.json `
  --region us-east-1
```

### Get VPC and Subnet Information

```powershell
# Get your default VPC
$VPC_ID = python -m aws ec2 describe-vpcs `
  --filters "Name=isDefault,Values=true" `
  --query "Vpcs[0].VpcId" `
  --output text `
  --region us-east-1

# Get a subnet in that VPC
$SUBNET_ID = python -m aws ec2 describe-subnets `
  --filters "Name=vpc-id,Values=$VPC_ID" `
  --query "Subnets[0].SubnetId" `
  --output text `
  --region us-east-1

# Get default security group
$SG_ID = python -m aws ec2 describe-security-groups `
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=default" `
  --query "SecurityGroups[0].GroupId" `
  --output text `
  --region us-east-1

# Save these for next step
Write-Host "VPC: $VPC_ID"
Write-Host "Subnet: $SUBNET_ID"
Write-Host "Security Group: $SG_ID"
```

### Update Security Group to Allow Port 8000

```powershell
# Allow inbound traffic on port 8000
python -m aws ec2 authorize-security-group-ingress `
  --group-id $SG_ID `
  --protocol tcp `
  --port 8000 `
  --cidr 0.0.0.0/0 `
  --region us-east-1
```

### Register ECS Task Definition

```powershell
# Get your account ID
$ACCOUNT_ID = python -m aws sts get-caller-identity --query Account --output text
$REPO_URI = "$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/mortgage-rate-notifier"

# Create task definition
@{
    family = "mortgage-rate-notifier-task"
    taskRoleArn = "arn:aws:iam::$($ACCOUNT_ID):role/ecsTaskExecutionRole-mortgage"
    executionRoleArn = "arn:aws:iam::$($ACCOUNT_ID):role/ecsTaskExecutionRole-mortgage"
    networkMode = "awsvpc"
    requiresCompatibilities = @("FARGATE")
    cpu = "256"
    memory = "512"
    containerDefinitions = @(
        @{
            name = "mortgage-rate-notifier"
            image = "$REPO_URI:latest"
            essential = $true
            portMappings = @(
                @{
                    containerPort = 8000
                    hostPort = 8000
                    protocol = "tcp"
                }
            )
            environment = @(
                @{
                    name = "ENVIRONMENT"
                    value = "production"
                }
                @{
                    name = "AWS_REGION"
                    value = "us-east-1"
                }
            )
            logConfiguration = @{
                logDriver = "awslogs"
                options = @{
                    "awslogs-group" = "/ecs/mortgage-rate-notifier"
                    "awslogs-region" = "us-east-1"
                    "awslogs-stream-prefix" = "ecs"
                }
            }
            healthCheck = @{
                command = @("CMD-SHELL", "curl -f http://localhost:8000/health || exit 1")
                interval = 30
                timeout = 5
                retries = 3
                startPeriod = 60
            }
        }
    )
} | ConvertTo-Json -Depth 5 | Out-File taskDefinition.json

# Register the task definition
python -m aws ecs register-task-definition `
  --cli-input-json file://taskDefinition.json `
  --region us-east-1
```

### Create ECS Service

```powershell
# Create the service that runs your application
python -m aws ecs create-service `
  --cluster mortgage-rate-notifier `
  --service-name mortgage-rate-notifier-service `
  --task-definition mortgage-rate-notifier-task `
  --desired-count 1 `
  --launch-type FARGATE `
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" `
  --region us-east-1
```

---

## ✅ Step 6: Verify Deployment

### Check Service Status

```powershell
# Check if service is running
python -m aws ecs describe-services `
  --cluster mortgage-rate-notifier `
  --services mortgage-rate-notifier-service `
  --region us-east-1 | ConvertFrom-Json | Select-Object -ExpandProperty services | Format-Table serviceName, status, desiredCount, runningCount
```

Expected output:
```
serviceName                        status  desiredCount runningCount
─────────────────────────────────  ──────  ────────────  ────────────
mortgage-rate-notifier-service     ACTIVE              1            1
```

### Get the Public IP Address

```powershell
# Get task details
$tasks = python -m aws ecs list-tasks `
  --cluster mortgage-rate-notifier `
  --region us-east-1 | ConvertFrom-Json

$task_arn = $tasks.taskArns[0]

# Describe the task to get network details
$task_details = python -m aws ecs describe-tasks `
  --cluster mortgage-rate-notifier `
  --tasks $task_arn `
  --region us-east-1 | ConvertFrom-Json

# Get network interface ID
$eni_id = $task_details.tasks[0].attachments | Where-Object name -eq "ElasticNetworkInterface" | Select-Object -First 1 | Select-Object -ExpandProperty details

# Find the public IP
python -m aws ec2 describe-network-interfaces `
  --network-interface-ids $eni_id.value `
  --region us-east-1 | ConvertFrom-Json | Select-Object -ExpandProperty NetworkInterfaces | Select-Object -ExpandProperty Association | Select-Object PublicIp
```

### Test Your Deployed API

```powershell
# Replace with the public IP from above
$PUBLIC_IP = "54.123.45.67"

# Test health endpoint
Invoke-WebRequest -Uri "http://$PUBLIC_IP:8000/health" | Select-Object StatusCode, @{Name="Body"; Expression={$_.Content | ConvertFrom-Json}}

# Test rates endpoint
Invoke-WebRequest -Uri "http://$PUBLIC_IP:8000/rates" | Select-Object StatusCode, @{Name="Body"; Expression={$_.Content | ConvertFrom-Json}}

# View API docs
Write-Host "Swagger UI: http://$PUBLIC_IP:8000/docs"
```

---

## 🔍 Monitoring and Logs

### View Application Logs

```powershell
# Stream logs in real-time
python -m aws logs tail /ecs/mortgage-rate-notifier --follow --region us-east-1
```

### Check CloudWatch Metrics

```powershell
# View CPU and memory usage
python -m aws cloudwatch get-metric-statistics `
  --namespace AWS/ECS `
  --metric-name CPUUtilization `
  --dimensions Name=ServiceName,Value=mortgage-rate-notifier-service Name=ClusterName,Value=mortgage-rate-notifier `
  --start-time (Get-Date).AddHours(-1) `
  --end-time (Get-Date) `
  --period 300 `
  --statistics Average `
  --region us-east-1
```

---

## 📊 What AWS Runs

✅ **Everything runs on AWS:**
- FastAPI REST API
- All endpoints
- RAG decision-making model
- Rate limiting
- FRED rate fetching
- All processing

✅ **Fully serverless with ECS Fargate:**
- No servers to manage
- Auto-scales (optional)
- Pay only for what you use
- $4-6/month on free tier

---

## 🆘 Troubleshooting

### Task Won't Start
```powershell
# Check task logs
python -m aws logs tail /ecs/mortgage-rate-notifier --region us-east-1
```

### Can't Connect to API
```powershell
# Verify security group allows port 8000
python -m aws ec2 describe-security-groups --group-ids $SG_ID --region us-east-1
```

### Still Having Issues?
Check these files:
- [RATE_LIMITING.md](../RATE_LIMITING.md) - Rate limiting info
- [PRODUCTION_SECURITY_GUIDE.md](../docs/PRODUCTION_SECURITY_GUIDE.md) - Security details
- Logs: `aws logs tail /ecs/mortgage-rate-notifier --follow`

---

## 💰 Cost Estimate

| Service | Cost | Notes |
|---------|------|-------|
| ECS Fargate | $0.015/hour | ~$3-4/month for 1 task 24/7 |
| CloudWatch Logs | $0.50/GB | Usually <$1/month |
| Parameter Store | Free | First 10,000 free |
| ECR Storage | Free | <1GB free tier |
| **Total** | **~$4-6/month** | Includes free tier |

---

## 🎉 You're Ready!

Your application is now deployed on AWS! 

**API will be available at:**
```
http://<PUBLIC_IP>:8000
```

**Key Endpoints:**
- `/health` - API health check
- `/rates` - Current mortgage rates
- `/rates/historical` - Historical rates
- `/decision` - Refinancing decisions
- `/docs` - API documentation

That's it! Your AI model is now running on AWS! 🚀
