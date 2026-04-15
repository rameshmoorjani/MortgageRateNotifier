# 📋 AWS Deployment Checklist

Complete guide for deploying Mortgage Rate Notifier to AWS with Parameter Store.

---

## ✅ Pre-Deployment Checklist

### Local Setup
- [ ] AWS CLI installed (`aws --version` works)
- [ ] boto3 installed in requirements.txt
- [ ] `src/config_aws.py` exists in your project
- [ ] `agents/rates_agent.py` updated to use Parameter Store
- [ ] `.env` file contains `FRED_API_KEY`
- [ ] `.env` is in `.gitignore` (never commit secrets!)

### AWS Account & Credentials
- [ ] AWS Account created
- [ ] Access Key ID obtained from IAM console
- [ ] Secret Access Key saved securely
- [ ] `aws configure` completed (your credentials are set)
- [ ] Verify credentials: `aws sts get-caller-identity` works

### API Keys & Secrets
- [ ] FRED API key ready: `YOUR-FRED-API-KEY-HERE`
- [ ] OpenAI API key obtained (if using RAG features)
- [ ] All keys stored safely (not in version control)

---

## 🚀 Step-by-Step Deployment

### Step 1: Store Secrets in AWS Parameter Store

```powershell
# Store FRED API key
aws ssm put-parameter `
  --name "/mortgage-rate-notifier/FRED_API_KEY" `
  --value "YOUR-FRED-API-KEY-HERE" `
  --type "SecureString" `
  --region us-east-1

# Store OpenAI API key (optional)
aws ssm put-parameter `
  --name "/mortgage-rate-notifier/OPENAI_API_KEY" `
  --value "sk-your-openai-key" `
  --type "SecureString" `
  --region us-east-1

# Verify FRED key stored
aws ssm get-parameter `
  --name "/mortgage-rate-notifier/FRED_API_KEY" `
  --with-decryption `
  --region us-east-1
```

- [ ] FRED_API_KEY stored
- [ ] OPENAI_API_KEY stored (optional)
- [ ] Both verified with get-parameter

---

### Step 2: Create ECR Repository

**Via CLI:**
```powershell
aws ecr create-repository `
  --repository-name mortgage-rate-notifier `
  --region us-east-1
```

**Or via AWS Console:**
1. Go to: https://console.aws.amazon.com/ecr
2. Click: "Get started" or "Create repository"
3. Name: `mortgage-rate-notifier`
4. Click: "Create repository"
5. Note the URI (you'll need it next)

- [ ] ECR repository created
- [ ] Repository URI noted

---

### Step 3: Build & Push Docker Image

```powershell
# Set variables
$AWS_ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
$REGION = "us-east-1"
$REPO_URI = "$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/mortgage-rate-notifier"

# Login to ECR
aws ecr get-login-password --region $REGION | `
  docker login --username AWS --password-stdin $REPO_URI

# Build Docker image
docker build -f docker/Dockerfile.production -t mortgage-rate-notifier:latest .

# Tag image for ECR
docker tag mortgage-rate-notifier:latest "$REPO_URI:latest"

# Push to ECR
docker push "$REPO_URI:latest"
```

- [ ] Docker image built
- [ ] Docker image pushed to ECR
- [ ] Can verify in AWS Console (ECR → Images)

---

### Step 4: Create ECS Cluster

```powershell
# Create Fargate cluster
aws ecs create-cluster `
  --cluster-name mortgage-rate-notifier `
  --region us-east-1
```

**Or via AWS Console:**
1. Go to: https://console.aws.amazon.com/ecs
2. Click: "Create cluster"
3. Name: `mortgage-rate-notifier`
4. Infrastructure: `AWS Fargate`
5. Click: "Create"

- [ ] ECS Cluster created
- [ ] Cluster name: `mortgage-rate-notifier`

---

### Step 5: Create IAM Role for ECS Tasks

```powershell
# Create role
$trust_policy = @{
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
} | ConvertTo-Json -Depth 2

$trust_policy | Out-File -FilePath trust-policy.json -Encoding utf8

aws iam create-role `
  --role-name ecsTaskExecutionRole-mortgage `
  --assume-role-policy-document file://trust-policy.json `
  --region us-east-1

# Attach required policies
aws iam attach-role-policy `
  --role-name ecsTaskExecutionRole-mortgage `
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Attach Parameter Store policy
$inline_policy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @(
                "ssm:GetParameter"
                "ssm:GetParameters"
            )
            Resource = "arn:aws:ssm:$REGION`:$AWS_ACCOUNT_ID`:parameter/mortgage-rate-notifier/*"
        }
        @{
            Effect = "Allow"
            Action = @(
                "kms:Decrypt"
            )
            Resource = "*"
        }
    )
} | ConvertTo-Json -Depth 2

$inline_policy | Out-File -FilePath parameter-policy.json -Encoding utf8

aws iam put-role-policy `
  --role-name ecsTaskExecutionRole-mortgage `
  --policy-name AllowParameterStore `
  --policy-document file://parameter-policy.json `
  --region us-east-1
```

- [ ] IAM Role created: `ecsTaskExecutionRole-mortgage`
- [ ] Policies attached
- [ ] Trust policy configured

---

### Step 6: Create ECS Task Definition

Save as `aws/task-definition.json`:

```json
{
  "family": "mortgage-rate-notifier-task",
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole-mortgage",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole-mortgage",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "mortgage-rate-notifier",
      "image": "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/mortgage-rate-notifier:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "AWS_REGION",
          "value": "us-east-1"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/mortgage-rate-notifier",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

Replace `ACCOUNT_ID` with your AWS Account ID:

```powershell
# Register task definition
aws ecs register-task-definition `
  --cli-input-json file://aws/task-definition.json `
  --region us-east-1
```

- [ ] Task definition file created (`aws/task-definition.json`)
- [ ] Account ID replaced in file
- [ ] Task definition registered

---

### Step 7: Create CloudWatch Log Group

```powershell
aws logs create-log-group `
  --log-group-name /ecs/mortgage-rate-notifier `
  --region us-east-1

aws logs put-retention-policy `
  --log-group-name /ecs/mortgage-rate-notifier `
  --retention-in-days 30 `
  --region us-east-1
```

- [ ] Log group created
- [ ] Retention policy set

---

### Step 8: Create ECS Service

```powershell
# Get VPC and subnet information
$vpc_id = aws ec2 describe-vpcs `
  --filters "Name=isDefault,Values=true" `
  --query "Vpcs[0].VpcId" `
  --output text `
  --region us-east-1

$subnet_id = aws ec2 describe-subnets `
  --filters "Name=vpc-id,Values=$vpc_id" `
  --query "Subnets[0].SubnetId" `
  --output text `
  --region us-east-1

$sg_id = aws ec2 describe-security-groups `
  --filters "Name=vpc-id,Values=$vpc_id" "Name=group-name,Values=default" `
  --query "SecurityGroups[0].GroupId" `
  --output text `
  --region us-east-1

# Create service
aws ecs create-service `
  --cluster mortgage-rate-notifier `
  --service-name mortgage-rate-notifier-service `
  --task-definition mortgage-rate-notifier-task `
  --desired-count 1 `
  --launch-type FARGATE `
  --network-configuration "awsvpcConfiguration={subnets=[$subnet_id],securityGroups=[$sg_id],assignPublicIp=ENABLED}" `
  --region us-east-1
```

- [ ] ECS Service created
- [ ] Desired count: 1
- [ ] Task is running (check AWS Console)

---

## 🎯 Verification

### Check Service Status

```powershell
# Get service details
aws ecs describe-services `
  --cluster mortgage-rate-notifier `
  --services mortgage-rate-notifier-service `
  --region us-east-1

# List running tasks
aws ecs list-tasks `
  --cluster mortgage-rate-notifier `
  --region us-east-1

# Get task details
aws ecs describe-tasks `
  --cluster mortgage-rate-notifier `
  --tasks (task-arn-from-list-tasks) `
  --region us-east-1
```

- [ ] Service status: `ACTIVE`
- [ ] Desired count: 1
- [ ] Running count: 1
- [ ] Task is in `RUNNING` state

### Check Logs

```powershell
# View logs
aws logs tail /ecs/mortgage-rate-notifier --follow --region us-east-1
```

- [ ] API started successfully
- [ ] No errors in logs
- [ ] Parameter Store access successful

### Test API Endpoint

```powershell
# Get task's public IP
$task_details = aws ecs describe-tasks `
  --cluster mortgage-rate-notifier `
  --tasks (task-arn) `
  --region us-east-1 | ConvertFrom-Json

$public_ip = $task_details.tasks[0].attachments[0].details | 
  Where-Object { $_.name -eq "networkInterfaceId" } | 
  ForEach-Object {
    aws ec2 describe-network-interfaces `
      --network-interface-ids $_.value `
      --region us-east-1 | 
      ConvertFrom-Json | 
      Select-Object -ExpandProperty NetworkInterfaces | 
      Select-Object -ExpandProperty Association | 
      Select-Object -ExpandProperty PublicIp
  }

# Test API
curl http://$public_ip:8000/rates?state=AZ

# Or in PowerShell
Invoke-WebRequest -Uri "http://$public_ip:8000/health"
```

- [ ] API responds with 200 status
- [ ] Health endpoint returns status
- [ ] `/rates` returns mortgage rates

---

## 💡 Next Steps (Optional)

### Add Load Balancer (Optional)

```powershell
# Create Application Load Balancer
aws elbv2 create-load-balancer `
  --name mortgage-rate-alb `
  --subnets $subnet_id `
  --security-groups $sg_id `
  --scheme internet-facing `
  --region us-east-1
```

### Add Custom Domain (Optional)

Use Route 53 to point your domain to the ECS task or load balancer.

### Enable Auto-Scaling (Optional)

Configure auto-scaling to add more tasks under high load.

---

## 🧹 Cleanup (Delete Everything)

If you want to remove all AWS resources:

```powershell
# Delete service
aws ecs delete-service --cluster mortgage-rate-notifier --service mortgage-rate-notifier-service --force --region us-east-1

# Delete cluster
aws ecs delete-cluster --cluster mortgage-rate-notifier --region us-east-1

# Delete task definition
aws ecs deregister-task-definition --task-definition mortgage-rate-notifier-task:1 --region us-east-1

# Delete ECR repository
aws ecr delete-repository --repository-name mortgage-rate-notifier --force --region us-east-1

# Delete log group
aws logs delete-log-group --log-group-name /ecs/mortgage-rate-notifier --region us-east-1

# Delete IAM role
aws iam delete-role-policy --role-name ecsTaskExecutionRole-mortgage --policy-name AllowParameterStore --region us-east-1
aws iam detach-role-policy --role-name ecsTaskExecutionRole-mortgage --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy --region us-east-1
aws iam delete-role --role-name ecsTaskExecutionRole-mortgage --region us-east-1
```

---

## 📚 Summary

| Step | Done | Status |
|------|------|--------|
| 1. Secrets in Parameter Store | [ ] | ⏳ |
| 2. ECR Repository | [ ] | ⏳ |
| 3. Docker Image Built & Pushed | [ ] | ⏳ |
| 4. ECS Cluster Created | [ ] | ⏳ |
| 5. IAM Role Created | [ ] | ⏳ |
| 6. Task Definition Registered | [ ] | ⏳ |
| 7. Log Group Created | [ ] | ⏳ |
| 8. ECS Service Running | [ ] | ⏳ |
| 9. API Verified Working | [ ] | ⏳ |

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Task won't start | Check logs: `aws logs tail /ecs/mortgage-rate-notifier` |
| Parameter not found | Verify Parameter Store: `aws ssm describe-parameters --region us-east-1` |
| Access denied | Check IAM role permissions attached to task |
| API not responding | Verify security group allows port 8000 inbound |
| High costs | Check CloudWatch logs and autoscaling settings |

---

**Your application is now running on AWS!** 🎉
