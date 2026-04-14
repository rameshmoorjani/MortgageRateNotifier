# 🔐 AWS Systems Manager Parameter Store Setup

Complete guide to store your FRED API key securely in AWS and deploy your application.

---

## 📋 Prerequisites

1. **AWS Account** (free tier eligible)
2. **AWS CLI** installed locally
3. **Your FRED API Key**: `YOUR-FRED-API-KEY-HERE`

---

## 🛠️ Step 1: Install AWS CLI

### On Windows:
```powershell
# Using Chocolatey (if installed)
choco install awscli

# Or download from: https://aws.amazon.com/cli/
# Then verify installation
aws --version
```

---

## 🔑 Step 2: Configure AWS Credentials

```powershell
# Configure your AWS account
aws configure

# When prompted, enter:
# AWS Access Key ID: (get from AWS console)
# AWS Secret Access Key: (get from AWS console)
# Default region: us-east-1
# Default output format: json
```

**Get your Access Keys:**
1. Go to: https://console.aws.amazon.com/
2. Login to your AWS account
3. Go to: IAM → Users → Your User → Security Credentials
4. Create Access Key
5. Copy the Access Key ID and Secret Access Key

---

## 💾 Step 3: Store API Keys in Parameter Store

### Using AWS CLI (Easiest):

```powershell
# Store FRED API Key
aws ssm put-parameter `
  --name "/mortgage-rate-notifier/FRED_API_KEY" `
  --value "YOUR-FRED-API-KEY-HERE" `
  --type "SecureString" `
  --region us-east-1

# Verify it was stored
aws ssm get-parameter `
  --name "/mortgage-rate-notifier/FRED_API_KEY" `
  --with-decryption `
  --region us-east-1
```

### Using AWS Console (Visual):

1. Go to: https://console.aws.amazon.com/
2. Search for: "Systems Manager"
3. Click: "Parameter Store"
4. Click: "Create parameter"
5. Fill in:
   - Name: `/mortgage-rate-notifier/FRED_API_KEY`
   - Type: `SecureString`
   - Value: `YOUR-FRED-API-KEY-HERE`
6. Click: "Create parameter"

---

## 📝 Step 4: Update Your Application Code

Your application needs to read from Parameter Store. I'll create a module for this.

**File: `src/config_aws.py`**

```python
import os
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class AWSParameterStore:
    """Fetch secrets from AWS Systems Manager Parameter Store"""
    
    def __init__(self, region='us-east-1'):
        self.region = region
        self.ssm = boto3.client('ssm', region_name=region)
        self.cache = {}
    
    def get_parameter(self, parameter_name, decrypt=True):
        """
        Get parameter from Parameter Store
        
        Args:
            parameter_name: Full parameter name (e.g., /mortgage-rate-notifier/FRED_API_KEY)
            decrypt: If True, decrypt SecureString parameters
        
        Returns:
            Parameter value or None if not found
        """
        if parameter_name in self.cache:
            return self.cache[parameter_name]
        
        try:
            response = self.ssm.get_parameter(
                Name=parameter_name,
                WithDecryption=decrypt
            )
            value = response['Parameter']['Value']
            self.cache[parameter_name] = value
            logger.info(f"✓ Retrieved parameter from Parameter Store: {parameter_name}")
            return value
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                logger.warning(f"Parameter not found: {parameter_name}")
            else:
                logger.error(f"Error retrieving parameter: {e}")
            return None
    
    def clear_cache(self):
        """Clear cached values"""
        self.cache.clear()


# Initialize Parameter Store client
parameter_store = AWSParameterStore(region=os.getenv('AWS_REGION', 'us-east-1'))


def get_fred_api_key():
    """Get FRED API key from environment or Parameter Store"""
    # First check environment variable (for local dev)
    if os.getenv('FRED_API_KEY'):
        logger.info("Using FRED API key from environment variable (local dev)")
        return os.getenv('FRED_API_KEY')
    
    # For production, use Parameter Store
    try:
        key = parameter_store.get_parameter('/mortgage-rate-notifier/FRED_API_KEY')
        if key:
            logger.info("Using FRED API key from AWS Parameter Store")
            return key
    except Exception as e:
        logger.error(f"Failed to get FRED API key from Parameter Store: {e}")
    
    logger.warning("FRED API key not found")
    return None


def get_openai_api_key():
    """Get OpenAI API key from environment or Parameter Store"""
    # First check environment variable (for local dev)
    if os.getenv('OPENAI_API_KEY'):
        logger.info("Using OpenAI API key from environment variable (local dev)")
        return os.getenv('OPENAI_API_KEY')
    
    # For production, use Parameter Store
    try:
        key = parameter_store.get_parameter('/mortgage-rate-notifier/OPENAI_API_KEY')
        if key:
            logger.info("Using OpenAI API key from AWS Parameter Store")
            return key
    except Exception as e:
        logger.error(f"Failed to get OpenAI API key from Parameter Store: {e}")
    
    logger.warning("OpenAI API key not found")
    return None
```

---

## 📦 Step 5: Install boto3

```powershell
# Add to requirements.txt
c:\python314\python.exe -m pip install boto3

# Or install directly
pip install boto3
```

**Update `requirements.txt`:**
```
# ... existing packages ...
boto3==1.26.89
botocore==1.29.89
```

---

## 🐳 Step 6: Docker Setup for AWS

Your existing `docker/Dockerfile` should work. Just ensure it includes boto3:

**`docker/Dockerfile`:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies (including boto3)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set environment
ENV ENVIRONMENT=production
ENV AWS_REGION=us-east-1

# Run API
CMD ["uvicorn", "src.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🚀 Step 7: Deploy to AWS ECS Fargate (Simplest)

### Option A: Using AWS Console (Visual)

1. **Create ECR Repository** (Docker image storage)
   - Go to: https://console.aws.amazon.com/ecr
   - Click: "Create repository"
   - Name: `mortgage-rate-notifier`
   - Click: "Create repository"

2. **Build and Push Docker Image**
   ```powershell
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

   # Build image
   docker build -f docker/Dockerfile -t mortgage-rate-notifier .

   # Tag image
   docker tag mortgage-rate-notifier:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/mortgage-rate-notifier:latest

   # Push to ECR
   docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/mortgage-rate-notifier:latest
   ```

3. **Create ECS Cluster**
   - Go to: https://console.aws.amazon.com/ecs
   - Click: "Create cluster"
   - Name: `mortgage-rate-notifier`
   - Infrastructure: Fargate
   - Click: "Create"

4. **Create Task Definition**
   - Click: "Create new task definition"
   - Name: `mortgage-rate-notifier-task`
   - Container name: `mortgage-rate-notifier`
   - Image: `YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/mortgage-rate-notifier:latest`
   - Port: `8000`
   - Environment variables:
     - `ENVIRONMENT=production`
     - `AWS_REGION=us-east-1`
   - Click: "Create"

5. **Create Service**
   - In your cluster, click: "Create service"
   - Task definition: `mortgage-rate-notifier-task`
   - Desired count: `1`
   - Click: "Create service"

---

### Option B: Using AWS CloudFormation (Infrastructure as Code)

Create file: `aws/cloudformation-template.yaml`

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Mortgage Rate Notifier - FastAPI Application on ECS Fargate'

Resources:
  # ECR Repository
  ECRRepository:
    Type: AWS::ECR::Repository
    Properties:
      RepositoryName: mortgage-rate-notifier
      ImageScanningConfiguration:
        ScanOnPush: true

  # ECS Cluster
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: mortgage-rate-notifier

  # Task Definition
  TaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      Family: mortgage-rate-notifier-task
      NetworkMode: awsvpc
      RequiresCompatibilities:
        - FARGATE
      Cpu: 256
      Memory: 512
      ContainerDefinitions:
        - Name: mortgage-rate-notifier
          Image: !Sub '${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/mortgage-rate-notifier:latest'
          PortMappings:
            - ContainerPort: 8000
          Environment:
            - Name: ENVIRONMENT
              Value: production
            - Name: AWS_REGION
              Value: !Ref AWS::Region
          LogConfiguration:
            LogDriver: awslogs
            Options:
              awslogs-group: !Ref LogGroup
              awslogs-region: !Ref AWS::Region
              awslogs-stream-prefix: ecs

  # CloudWatch Log Group
  LogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: /ecs/mortgage-rate-notifier
      RetentionInDays: 30

  # Service
  ECSService:
    Type: AWS::ECS::Service
    Properties:
      ServiceName: mortgage-rate-notifier-service
      Cluster: !Ref ECSCluster
      TaskDefinition: !Ref TaskDefinition
      DesiredCount: 1
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          AssignPublicIp: ENABLED
          Subnets:
            - subnet-12345678  # Update with your subnet
          SecurityGroups:
            - sg-12345678     # Update with your security group

Outputs:
  ECRRepository:
    Value: !GetAtt ECRRepository.RepositoryUri
  ECSCluster:
    Value: !GetAtt ECSCluster.ClusterName
  ECSService:
    Value: !GetAtt ECSService.ServiceName
```

Deploy:
```powershell
aws cloudformation create-stack `
  --stack-name mortgage-rate-notifier `
  --template-body file://aws/cloudformation-template.yaml `
  --region us-east-1
```

---

## 🔒 IAM Permissions (Important!)

Your ECS Task needs permissions to read from Parameter Store.

Create IAM Policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters"
      ],
      "Resource": "arn:aws:ssm:us-east-1:YOUR_ACCOUNT_ID:parameter/mortgage-rate-notifier/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt"
      ],
      "Resource": "arn:aws:kms:us-east-1:YOUR_ACCOUNT_ID:key/*"
    }
  ]
}
```

Attach to ECS Task Role in the AWS Console.

---

## 📊 Summary

| Step | Action | Status |
|------|--------|--------|
| 1 | Install AWS CLI | 📝 Do this |
| 2 | Configure credentials | 📝 Do this |
| 3 | Store API keys in Parameter Store | 📝 Do this |
| 4 | Update application code | ✅ I'll help |
| 5 | Install boto3 | 📝 Do this |
| 6 | Build Docker image | 📝 Do this |
| 7 | Deploy to ECS Fargate | 📝 Do this |

---

## ✅ Testing Locally Before Deploying

```powershell
# Test Parameter Store locally
$env:AWS_REGION = "us-east-1"
c:\python314\python.exe -c "
from src.config_aws import get_fred_api_key
key = get_fred_api_key()
print(f'FRED API Key: {key[:10]}...' if key else 'Key not found')
"
```

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Parameter not found | Ensure you created it in Parameter Store with correct name |
| Access denied | Check IAM permissions for ECS task role |
| Docker image fails | Ensure boto3 is in requirements.txt |
| Can't connect to AWS | Check AWS credentials with `aws sts get-caller-identity` |

---

## 📚 Additional Resources

- [AWS Systems Manager Parameter Store Docs](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- [ECS Fargate Getting Started](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/getting-started-fargate.html)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

---

**You're ready to deploy securely to AWS!** 🚀
