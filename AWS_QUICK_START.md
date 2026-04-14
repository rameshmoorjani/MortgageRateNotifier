# 🚀 AWS Parameter Store - Quick Start

Get your application running on AWS in 10 minutes.

---

## ⚡ TL;DR - 5 Quick Commands

```powershell
# 1. Install AWS CLI
# Go to: https://aws.amazon.com/cli/
# Download and install (or use: choco install awscli)

# 2. Configure AWS
aws configure
# Enter your Access Key ID, Secret Access Key, and region: us-east-1

# 3. Store your FRED API key
aws ssm put-parameter --name "/mortgage-rate-notifier/FRED_API_KEY" --value "YOUR-FRED-API-KEY-HERE" --type "SecureString" --region us-east-1

# 4. Verify it was stored
aws ssm get-parameter --name "/mortgage-rate-notifier/FRED_API_KEY" --with-decryption --region us-east-1

# 5. Test locally
$env:AWS_REGION = "us-east-1"
python src/config_aws.py
```

That's it! Your API key is now securely stored in AWS. 🔐

---

## 📖 Next Steps

### For Local Development

Your application will automatically:
1. Check `.env` file for `FRED_API_KEY` (development)
2. Fall back to AWS Parameter Store (production)

**No code changes needed!** The `rates_agent.py` has been updated to handle both.

### For Production Deployment

When you deploy to AWS:

1. **Don't include your `.env` file** in the Docker image
2. The application will automatically read from Parameter Store
3. Your ECS task needs IAM permissions (see AWS_PARAMETER_STORE_DEPLOY.md)

---

## 🔧 Testing Parameter Store Access

```powershell
# Test that you can access Parameter Store
python -c "from src.config_aws import get_fred_api_key; print(get_fred_api_key())"
```

If it works:
- Shows your API key? ✓ You're connected to AWS
- Shows None? That's OK - Parameter Store is only needed in production

---

## 📝 What Was Changed?

| File | Change |
|------|--------|
| `src/config_aws.py` | ✅ **CREATED** - New module for AWS Parameter Store |
| `agents/rates_agent.py` | ✅ **UPDATED** - Now reads from Parameter Store in production |
| `requirements.txt` | ✅ **UPDATED** - Added boto3 and botocore |
| `AWS_PARAMETER_STORE_DEPLOY.md` | ✅ **CREATED** - Complete deployment guide |

---

## 🆘 Troubleshooting

### "Parameter not found"

Your key isn't stored yet. Run:
```powershell
aws ssm put-parameter --name "/mortgage-rate-notifier/FRED_API_KEY" --value "YOUR_KEY_HERE" --type "SecureString" --region us-east-1
```

### "Access Denied"

Your AWS credentials aren't configured. Run:
```powershell
aws configure
```

Then verify:
```powershell
aws sts get-caller-identity
```

### boto3 import error

Install boto3:
```powershell
pip install boto3
```

---

## 📚 File Reference

**New files created:**

1. **`src/config_aws.py`** - AWS Parameter Store client
   - Use: `from src.config_aws import get_fred_api_key`
   - Handles environment variables and Parameter Store

2. **`AWS_PARAMETER_STORE_DEPLOY.md`** - Full deployment guide
   - Complete AWS setup instructions
   - Docker configuration
   - ECS Fargate deployment steps
   - IAM permissions setup

---

## ✅ You're Ready!

Your system now:
- ✓ Loads API keys securely from AWS Parameter Store (production)
- ✓ Falls back to `.env` file (local development)
- ✓ Has no hardcoded secrets
- ✓ Is ready for Docker deployment
- ✓ Is AWS deployment-ready

**Next step:** Follow the full guide in `AWS_PARAMETER_STORE_DEPLOY.md` when you're ready to deploy to AWS. 🚀
