# 🔐 Production Deployment - Secure Parameter Storage

Your API key is now securely stored locally in `.env` (which is in `.gitignore`).  
For production deployment, here's how to use **secure parameter stores** instead of environment files.

---

## 🏗️ Production Options

### **Option 1: AWS Systems Manager Parameter Store** (Recommended for AWS)

#### Setup:
```bash
# Store your API key in AWS Parameter Store
aws ssm put-parameter \
  --name /mortgage-rate-notifier/FRED_API_KEY \
  --value "YOUR-FRED-API-KEY-HERE" \
  --type SecureString
```

#### Your Application Code:
```python
import boto3
import os

def get_fred_api_key():
    """Get FRED API key from AWS Parameter Store"""
    # First check environment (for local dev)
    if os.getenv('FRED_API_KEY'):
        return os.getenv('FRED_API_KEY')
    
    # For production, use Parameter Store
    ssm = boto3.client('ssm')
    try:
        response = ssm.get_parameter(
            Name='/mortgage-rate-notifier/FRED_API_KEY',
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except Exception as e:
        logger.error(f"Failed to get FRED API key from Parameter Store: {e}")
        return None
```

---

### **Option 2: Azure Key Vault** (Recommended for Azure)

#### Setup via Azure CLI:
```bash
# Store your API key in Azure Key Vault
az keyvault secret set \
  --vault-name your-vault-name \
  --name FRED-API-KEY \
  --value "YOUR-FRED-API-KEY-HERE"
```

#### Your Application Code:
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os

def get_fred_api_key():
    """Get FRED API key from Azure Key Vault"""
    # First check environment (for local dev)
    if os.getenv('FRED_API_KEY'):
        return os.getenv('FRED_API_KEY')
    
    # For production, use Key Vault
    credential = DefaultAzureCredential()
    client = SecretClient(
        vault_url="https://your-vault-name.vault.azure.net/",
        credential=credential
    )
    try:
        secret = client.get_secret("FRED-API-KEY")
        return secret.value
    except Exception as e:
        logger.error(f"Failed to get FRED API key from Key Vault: {e}")
        return None
```

---

### **Option 3: Docker Secrets** (For Docker Swarm)

#### In your docker-compose.yml:
```yaml
version: '3.1'

services:
  api:
    image: mortgage-rate-notifier:latest
    environment:
      - FREDSECRETSFILE=/run/secrets/fred_api_key
    secrets:
      - fred_api_key

secrets:
  fred_api_key:
    external: true
    # Create with: docker secret create fred_api_key -
    # Then: echo "YOUR-FRED-API-KEY-HERE" | docker secret create fred_api_key -
```

#### Your Application Code:
```python
import os

def get_fred_api_key():
    """Get FRED API key from Docker secrets or environment"""
    # First check environment (for local dev)
    if os.getenv('FRED_API_KEY'):
        return os.getenv('FRED_API_KEY')
    
    # For Docker Swarm, read from secrets file
    secrets_file = os.getenv('FREDSECRETSFILE')
    if secrets_file and os.path.exists(secrets_file):
        with open(secrets_file, 'r') as f:
            return f.read().strip()
    
    return None
```

---

### **Option 4: Kubernetes Secrets**

#### Create secret:
```bash
kubectl create secret generic fred-api-key \
  --from-literal=api-key=YOUR-FRED-API-KEY-HERE
```

#### In your deployment.yaml:
```yaml
apiVersion: v1
kind: Deployment
metadata:
  name: mortgage-rate-notifier
spec:
  containers:
  - name: api
    image: mortgage-rate-notifier:latest
    env:
    - name: FRED_API_KEY
      valueFrom:
        secretKeyRef:
          name: fred-api-key
          key: api-key
```

---

### **Option 5: Railway/Heroku Environment Variables**

Both platforms allow you to set environment variables in their dashboards:

#### Railway:
1. Go to your project
2. Variables (tab)
3. Add new variable:
   - Key: `FRED_API_KEY`
   - Value: `YOUR-FRED-API-KEY-HERE`
4. Deploy

#### Heroku:
```bash
heroku config:set FRED_API_KEY=YOUR-FRED-API-KEY-HERE
```

---

## 🔄 Universal Solution (Works Everywhere)

Here's code that works with **all methods** above:

```python
import os
import logging

logger = logging.getLogger(__name__)

def get_fred_api_key():
    """
    Get FRED API key from multiple sources in order:
    1. Environment variable (local dev)
    2. AWS Parameter Store (if boto3 available)
    3. Azure Key Vault (if azure-identity available)
    4. File path (Docker Secrets, Kubernetes)
    """
    
    # 1. Check direct environment variable (development)
    api_key = os.getenv('FRED_API_KEY')
    if api_key and api_key.startswith('6'):  # Your actual key starts with 6
        logger.info("Using FRED API key from environment")
        return api_key
    
    # 2. Check AWS Parameter Store
    try:
        import boto3
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(
            Name='/mortgage-rate-notifier/FRED_API_KEY',
            WithDecryption=True
        )
        logger.info("Using FRED API key from AWS Parameter Store")
        return response['Parameter']['Value']
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"AWS Parameter Store not available: {e}")
    
    # 3. Check Azure Key Vault
    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient
        
        credential = DefaultAzureCredential()
        client = SecretClient(
            vault_url="https://your-vault-name.vault.azure.net/",
            credential=credential
        )
        secret = client.get_secret("FRED-API-KEY")
        logger.info("Using FRED API key from Azure Key Vault")
        return secret.value
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"Azure Key Vault not available: {e}")
    
    # 4. Check file path (Docker Secrets, Kubernetes)
    secrets_file = os.getenv('FREDSECRETSFILE')
    if secrets_file and os.path.exists(secrets_file):
        try:
            with open(secrets_file, 'r') as f:
                key = f.read().strip()
                logger.info("Using FRED API key from secrets file")
                return key
        except Exception as e:
            logger.debug(f"Secrets file not available: {e}")
    
    # 5. Return None if not found
    logger.warning("FRED API key not found in any secure location")
    return None
```

---

## 🚀 Implementation Steps

### For Your Current Setup:

1. ✅ **Local Development** (Done!)
   - Created `.env` with your FRED API key
   - `.env` is in `.gitignore` (safe to commit)

2. **Docker Deployment**
   - Update `docker/Dockerfile` to use the universal function above
   - Set environment variable when running: `docker run -e FRED_API_KEY=...`

3. **Cloud Deployment** (Pick one)
   - AWS: Use Parameter Store with boto3
   - Azure: Use Key Vault with azure-identity
   - Railway/Heroku: Use dashboard to set env vars

---

## ✅ Your Current Status

| Environment | Key Storage | Status |
|-------------|-------------|--------|
| **Local Dev** | `.env` file | ✅ Ready |
| **Docker** | Environment var | 📝 Configure when needed |
| **AWS** | Parameter Store | 📝 Configure when needed |
| **Azure** | Key Vault | 📝 Configure when needed |
| **Kubernetes** | Secrets | 📝 Configure when needed |

---

## 🔒 Security Best Practices

1. **Never commit `.env`** ✅ Already in `.gitignore`
2. **Use HTTPS only** ✅ FastAPI supports it
3. **Rotate API keys regularly** - Consider doing this quarterly
4. **Audit access** - Monitor who accesses your API key
5. **Use least privilege** - Only grant necessary permissions

---

## 🎯 Next Step

Your system is **ready to deploy**! When you're ready to push to production, just:

1. Choose your deployment platform (AWS, Azure, Railway, Docker, etc.)
2. Use the appropriate method from above to store your FRED API key
3. Update your code to use `get_fred_api_key()` function
4. Deploy without `.env` file

---

**Summary**: You're all set for **secure, production-ready deployment** with zero hardcoded secrets! 🚀
