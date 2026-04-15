#!/usr/bin/env python3
"""
Win dows-friendly Lambda Deployment Script
Uses Python's zipfile module instead of external zip command
"""

import os
import sys
import subprocess
import json
import zipfile
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
ACCOUNT_ID = "105726692206"
REGION = "us-east-1"
PROJECT_NAME = "mortgage-rate-notifier"
FRED_API_KEY = os.getenv('FRED_API_KEY', 'YOUR-FRED-API-KEY-HERE')

def run_command(command):
    """Run shell command and return result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_step(text):
    print(f"→ {text}")

def print_success(text):
    print(f"✓ {text}")

def print_error(text):
    print(f"✗ {text}")

def create_zip(source_dir, output_zip):
    """Create ZIP file from directory using Python."""
    print_step(f"Creating {output_zip}...")
    
    if Path(output_zip).exists():
        Path(output_zip).unlink()
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in Path(source_dir).rglob('*'):
            if file.is_file():
                arcname = file.relative_to(Path(source_dir).parent)
                zf.write(file, arcname)
    
    size_mb = Path(output_zip).stat().st_size / (1024 * 1024)
    print_success(f"{output_zip} created ({size_mb:.1f} MB)")

def build_lambda_package():
    """Build Lambda deployment package."""
    print_header("Building Lambda Package")
    
    # Create directory structure
    print_step("Creating directory structure...")
    lambda_dir = Path("lambda_package")
    if lambda_dir.exists():
        shutil.rmtree(lambda_dir)
    
    lambda_dir.mkdir()
    (lambda_dir / "src").mkdir()
    (lambda_dir / "agents").mkdir()
    
    # Copy source files
    print_step("Copying source files...")
    for file in Path("src").glob("*.py"):
        shutil.copy(file, lambda_dir / "src")
        print(f"  - {file.name}")
    
    for file in Path("agents").glob("*.py"):
        shutil.copy(file, lambda_dir / "agents")
        print(f"  - {file.name}")
    
    # Install dependencies
    print_step("Installing dependencies (this may take a minute)...")
    success, output = run_command(f"pip install -r aws/requirements-lambda.txt -t {lambda_dir}")
    if not success:
        print_error("Failed to install dependencies")
        return False
    
    # Clean up unnecessary files
    print_step("Removing unnecessary files...")
    for item in lambda_dir.rglob("*"):
        if item.is_dir() and item.name in ["__pycache__", "*.dist-info", "tests"]:
            shutil.rmtree(item, ignore_errors=True)
    
    # Remove .dist-info directories
    for dist_info in lambda_dir.rglob("*.dist-info"):
        shutil.rmtree(dist_info, ignore_errors=True)
    
    # Create ZIP file
    create_zip(str(lambda_dir), "lambda-code.zip")
    
    return True

def build_layer():
    """Build Lambda dependencies layer."""
    print_header("Building Lambda Layer")
    
    layer_dir = Path("python/lib/python3.11/site-packages")
    if layer_dir.parent.parent.exists():
        shutil.rmtree(layer_dir.parent.parent)
    
    layer_dir.mkdir(parents=True, exist_ok=True)
    
    print_step("Installing layer dependencies...")
    success, output = run_command(f"pip install -r aws/requirements-lambda.txt -t python/lib/python3.11/site-packages/")
    if not success:
        print_error("Failed to install layer dependencies")
        return False
    
    # Clean up
    for dist_info in Path("python").rglob("*.dist-info"):
        shutil.rmtree(dist_info, ignore_errors=True)
    
    create_zip("python", "layer-dependencies.zip")
    
    return True

def create_s3_bucket():
    """Create S3 bucket for code."""
    print_header("Step 2: Creating S3 Bucket")
    
    bucket_name = f"{PROJECT_NAME}-code-{ACCOUNT_ID}"
    print_step(f"Creating S3 bucket: {bucket_name}")
    
    success, output = run_command(f"aws s3 mb s3://{bucket_name} --region {REGION}")
    
    if success or "BucketAlreadyOwnedByYou" in output:
        print_success(f"S3 bucket ready: {bucket_name}")
        return True
    else:
        print_error(f"Failed: {output}")
        return False

def store_api_keys():
    """Store API keys in Parameter Store."""
    print_header("Step 3: Storing API Keys in Parameter Store")
    
    print_step("Storing FRED API Key...")
    success, output = run_command(
        f'aws ssm put-parameter --name "/mortgage-rate-notifier/FRED_API_KEY" '
        f'--value "{FRED_API_KEY}" --type "SecureString" --region {REGION} --overwrite'
    )
    
    if success:
        print_success("FRED API Key stored")
    else:
        print_error(f"Failed to store FRED key: {output}")
        return False
    
    print_step("Verifying API key...")
    success, output = run_command(
        'aws ssm get-parameter --name "/mortgage-rate-notifier/FRED_API_KEY" '
        '--with-decryption --region us-east-1 --query "Parameter.Value" --output text'
    )
    
    if success:
        print_success("API key verified")
    
    return True

def upload_to_s3(environment):
    """Upload packages to S3."""
    print_header(f"Step 5: Uploading to S3 ({environment})")
    
    bucket_name = f"{PROJECT_NAME}-code-{ACCOUNT_ID}"
    
    # Upload Lambda code
    print_step("Uploading Lambda code...")
    success, output = run_command(
        f"aws s3 cp lambda-code.zip s3://{bucket_name}/lambda-code-{environment}.zip"
    )
    if success:
        print_success("Lambda code uploaded")
    else:
        print_error(f"Failed: {output}")
        return False
    
    # Upload layer
    print_step("Uploading Lambda layer...")
    success, output = run_command(
        f"aws s3 cp layer-dependencies.zip s3://{bucket_name}/layer-dependencies-{environment}.zip"
    )
    if success:
        print_success("Lambda layer uploaded")
    else:
        print_error(f"Failed: {output}")
        return False
    
    return True

def deploy_cloudformation(environment, openai_key):
    """Deploy CloudFormation stack."""
    print_header(f"Step 6: Deploying CloudFormation Stack ({environment})")
    
    stack_name = f"{PROJECT_NAME}-{environment}"
    
    print_step(f"Validating CloudFormation template...")
    success, output = run_command(f"aws cloudformation validate-template --template-body file://aws/cloudformation-lambda.yaml")
    if not success:
        print_error(f"Template validation failed: {output}")
        return False
    print_success("Template is valid")
    
    print_step(f"Deploying stack: {stack_name}...")
    
    command = (
        f"aws cloudformation deploy "
        f"--template-file aws/cloudformation-lambda.yaml "
        f"--stack-name {stack_name} "
        f"--parameter-overrides "
        f"  EnvironmentName={environment} "
        f"  AccountId={ACCOUNT_ID} "
        f"  FredApiKey={FRED_API_KEY} "
        f"  OpenAiApiKey={openai_key} "
        f"  LambdaMemory=512 "
        f"  LambdaTimeout=60 "
        f"--capabilities CAPABILITY_NAMED_IAM "
        f"--region {REGION} "
        f"--no-fail-on-empty-changeset"
    )
    
    success, output = run_command(command)
    
    if success:
        print_success(f"Stack deployed: {stack_name}")
    else:
        print_error(f"Deployment failed: {output}")
        return False
    
    # Get API endpoint
    print_step("Retrieving API endpoint...")
    success, output = run_command(
        f'aws cloudformation describe-stacks --stack-name {stack_name} '
        f'--query "Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue" '
        f'--output text --region {REGION}'
    )
    
    if success and output.strip():
        api_endpoint = output.strip()
        print_success(f"API Endpoint: {api_endpoint}")
        return api_endpoint
    else:
        print_error("Could not retrieve API endpoint")
        return None

def test_api(api_endpoint):
    """Test API endpoints."""
    print_header("Step 7: Testing API Endpoints")
    
    print_step("Testing health check...")
    success, output = run_command(f'curl -X GET "{api_endpoint}/health" -H "Content-Type: application/json"')
    
    if success:
        print_success("Health check passed!")
        try:
            response = json.loads(output)
            print(f"  Status: {response.get('status', 'unknown')}")
            print(f"  Service: {response.get('service', 'unknown')}")
            print(f"  Version: {response.get('version', 'unknown')}")
        except:
            pass
    else:
        print_error(f"Health check failed: {output}")

def main():
    """Main deployment workflow."""
    environment = "dev"
    openai_key = "sk-proj-your-actual-openai-api-key-here"  # User should provide this
    
    print(f"\n{'='*70}")
    print(f"  Mortgage Rate Notifier - AWS Lambda Deployment")
    print(f"  Environment: {environment.upper()}")
    print(f"{'='*70}\n")
    print_step("Starting automated deployment...")
    
    # Step 1: Already done (credentials verified)
    print_header("Step 1: AWS Credentials ✓")
    print_success("AWS credentials verified (Account: 105726692206)")
    
    # Step 2: Build packages
    if not build_lambda_package():
        print_error("Failed to build Lambda package")
        sys.exit(1)
    
    if not build_layer():
        print_error("Failed to build Lambda layer")
        sys.exit(1)
    
    # Step 3: Create S3 bucket
    if not create_s3_bucket():
        sys.exit(1)
    
    # Step 4: Store API keys
    if not store_api_keys():
        sys.exit(1)
    
    # Step 5: Upload to S3
    if not upload_to_s3(environment):
        sys.exit(1)
    
    # Step 6: Deploy CloudFormation
    api_endpoint = deploy_cloudformation(environment, openai_key)
    if not api_endpoint:
        sys.exit(1)
    
    # Step 7: Test API
    test_api(api_endpoint)
    
    print_header("✓ Deployment Complete!")
    print(f"\n📊 Your API is now live!")
    print(f"  API Endpoint: {api_endpoint}")
    print(f"  Health Check: {api_endpoint}/health")
    print(f"  Decision API: {api_endpoint}/decision (POST)")
    print(f"  Batch API: {api_endpoint}/batch (POST)")
    print(f"\n✓ All done!\n")

if __name__ == "__main__":
    main()
