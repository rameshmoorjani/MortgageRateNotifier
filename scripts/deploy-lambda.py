#!/usr/bin/env python3
"""
Quick Lambda Deployment Script for Mortgage Rate Notifier

Automates the deployment process to AWS Lambda with minimal configuration.

Usage:
    python deploy-lambda.py --environment dev --action deploy
    python deploy-lambda.py --environment prod --action update-code
"""

import os
import sys
import subprocess
import json
import argparse
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# Configuration
ACCOUNT_ID = "105726692206"
REGION = "us-east-1"
PROJECT_NAME = "mortgage-rate-notifier"
FRED_API_KEY = os.getenv('FRED_API_KEY', 'YOUR-FRED-API-KEY-HERE')

# Colors for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print formatted header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{text}{Colors.ENDC}")
    print("=" * 70)

def print_step(text):
    """Print step text."""
    print(f"{Colors.BLUE}→{Colors.ENDC} {text}")

def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.ENDC} {text}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.ENDC} {text}")

def run_command(command, shell=False):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def check_prerequisites():
    """Check if all prerequisites are installed."""
    print_header("Checking Prerequisites")
    
    prerequisites = {
        "AWS CLI": "aws --version",
        "Python 3.11+": "python --version",
        "pip": "pip --version",
        "zip": "zip -v" if sys.platform != "win32" else "where zip",
    }
    
    all_ok = True
    for name, command in prerequisites.items():
        success, output = run_command(command, shell=True)
        if success:
            print_success(f"{name}: {output.strip()}")
        else:
            print_error(f"{name}: NOT FOUND")
            all_ok = False
    
    return all_ok

def create_s3_bucket():
    """Create S3 bucket for Lambda code."""
    print_step("Creating S3 bucket...")
    
    bucket_name = f"{PROJECT_NAME}-code-{ACCOUNT_ID}"
    
    success, output = run_command(
        f"aws s3 mb s3://{bucket_name} --region {REGION}",
        shell=True
    )
    
    if success or "BucketAlreadyOwnedByYou" in output:
        print_success(f"S3 bucket ready: {bucket_name}")
        return True
    else:
        print_error(f"Failed to create S3 bucket: {output}")
        return False

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
    
    for file in Path("agents").glob("*.py"):
        shutil.copy(file, lambda_dir / "agents")
    
    # Install dependencies
    print_step("Installing dependencies (this may take a minute)...")
    success, output = run_command(
        f"pip install -r aws/requirements-lambda.txt -t {lambda_dir}",
        shell=True
    )
    if not success:
        print_error(f"Failed to install dependencies")
        return False
    
    # Clean up unnecessary files
    print_step("Removing unnecessary files...")
    for pattern in ["*.dist-info", "__pycache__", "tests"]:
        for path in lambda_dir.rglob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    
    # Create ZIP file
    print_step("Creating ZIP file...")
    zip_path = Path("lambda-code.zip")
    if zip_path.exists():
        zip_path.unlink()
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in lambda_dir.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(lambda_dir.parent)
                zf.write(file, arcname)
    
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print_success(f"Lambda package created: {size_mb:.1f} MB")
    
    return True

def build_lambda_layer():
    """Build Lambda layer for dependencies."""
    print_step("Building Lambda layer...")
    
    # Create layer structure
    layer_dir = Path("python/lib/python3.11/site-packages")
    if layer_dir.parent.exists():
        shutil.rmtree(layer_dir.parent.parent)
    
    layer_dir.mkdir(parents=True)
    
    # Install dependencies into layer
    print_step("Installing layer dependencies...")
    success, output = run_command(
        f"pip install -r aws/requirements-lambda.txt -t {layer_dir}",
        shell=True
    )
    if not success:
        print_error("Failed to install layer dependencies")
        return False
    
    # Create ZIP file
    print_step("Creating layer ZIP file...")
    zip_path = Path("layer-dependencies.zip")
    if zip_path.exists():
        zip_path.unlink()
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in Path("python").rglob("*"):
            if file.is_file():
                arcname = file.relative_to(Path("python").parent)
                zf.write(file, arcname)
    
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print_success(f"Lambda layer created: {size_mb:.1f} MB")
    
    return True

def upload_to_s3(environment):
    """Upload packages to S3."""
    print_header(f"Uploading to S3 ({environment})")
    
    bucket_name = f"{PROJECT_NAME}-code-{ACCOUNT_ID}"
    
    # Upload Lambda code
    print_step("Uploading Lambda code...")
    success, output = run_command(
        f"aws s3 cp lambda-code.zip s3://{bucket_name}/lambda-code-{environment}.zip",
        shell=True
    )
    if not success:
        print_error(f"Failed to upload Lambda code")
        return False
    print_success("Lambda code uploaded")
    
    # Upload layer
    print_step("Uploading Lambda layer...")
    success, output = run_command(
        f"aws s3 cp layer-dependencies.zip s3://{bucket_name}/layer-dependencies-{environment}.zip",
        shell=True
    )
    if not success:
        print_error(f"Failed to upload layer")
        return False
    print_success("Lambda layer uploaded")
    
    return True

def deploy_cloudformation(environment, openai_key):
    """Deploy CloudFormation stack."""
    print_header(f"Deploying CloudFormation Stack ({environment})")
    
    stack_name = f"{PROJECT_NAME}-{environment}"
    
    print_step(f"Deploying stack: {stack_name}...")
    
    # Map environment to memory and timeout
    config = {
        "dev": {"memory": 512, "timeout": 60},
        "staging": {"memory": 1024, "timeout": 120},
        "prod": {"memory": 2048, "timeout": 300}
    }
    
    cfg = config.get(environment, config["dev"])
    
    command = [
        "aws", "cloudformation", "deploy",
        "--template-file", "aws/cloudformation-lambda.yaml",
        "--stack-name", stack_name,
        "--parameter-overrides",
        f"EnvironmentName={environment}",
        f"AccountId={ACCOUNT_ID}",
        f"FredApiKey={FRED_API_KEY}",
        f"OpenAiApiKey={openai_key}",
        f"LambdaMemory={cfg['memory']}",
        f"LambdaTimeout={cfg['timeout']}",
        "--capabilities", "CAPABILITY_NAMED_IAM",
        "--region", REGION,
        "--no-fail-on-empty-changeset"
    ]
    
    success, output = run_command(" ".join(command), shell=True)
    
    if not success:
        print_error(f"Deployment failed: {output}")
        return False
    
    print_success(f"Stack deployed: {stack_name}")
    
    # Get API endpoint
    print_step("Getting API endpoint...")
    success, output = run_command(
        f"aws cloudformation describe-stacks "
        f"--stack-name {stack_name} "
        f"--query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' "
        f"--output text "
        f"--region {REGION}",
        shell=True
    )
    
    if success and output.strip():
        api_endpoint = output.strip()
        print_success(f"API Endpoint: {api_endpoint}")
        return api_endpoint
    else:
        print_error("Could not retrieve API endpoint")
        return None

def test_api(api_endpoint):
    """Test the API endpoint."""
    print_header("Testing API")
    
    print_step("Testing health endpoint...")
    
    success, output = run_command(
        f"curl -X GET '{api_endpoint}/health' "
        f"-H 'Content-Type: application/json' "
        f"-w '\\nStatus: %{{http_code}}\\n'",
        shell=True
    )
    
    if success:
        print_success("Health check passed!")
        print(output)
    else:
        print_error(f"Health check failed: {output}")

def main():
    """Main deployment workflow."""
    parser = argparse.ArgumentParser(description="Deploy Mortgage Rate Notifier to AWS Lambda")
    parser.add_argument(
        "--environment",
        choices=["dev", "staging", "prod"],
        default="dev",
        help="Deployment environment"
    )
    parser.add_argument(
        "--action",
        choices=["deploy", "update-code", "test"],
        default="deploy",
        help="Action to perform"
    )
    parser.add_argument(
        "--openai-key",
        required=False,
        help="OpenAI API key"
    )
    
    args = parser.parse_args()
    
    print(f"\n{Colors.BOLD}{Colors.YELLOW}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   Mortgage Rate Notifier - AWS Lambda Deployment           ║")
    print("║   Environment: " + args.environment.upper().ljust(45) + "║")
    print("║   Action: " + args.action.ljust(50) + "║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(Colors.ENDC)
    
    # Check prerequisites
    if not check_prerequisites():
        print_error("Please install missing prerequisites and try again")
        sys.exit(1)
    
    # Perform action
    if args.action == "deploy":
        # Full deployment
        if not create_s3_bucket():
            sys.exit(1)
        
        if not build_lambda_package():
            sys.exit(1)
        
        if not build_lambda_layer():
            sys.exit(1)
        
        if not upload_to_s3(args.environment):
            sys.exit(1)
        
        openai_key = args.openai_key or input("Enter OpenAI API Key: ")
        api_endpoint = deploy_cloudformation(args.environment, openai_key)
        
        if api_endpoint:
            test_api(api_endpoint)
            print_header("✓ Deployment Complete!")
            print(f"API Endpoint: {api_endpoint}")
        else:
            sys.exit(1)
    
    elif args.action == "update-code":
        # Update only the code (not infrastructure)
        if not build_lambda_package():
            sys.exit(1)
        
        if not upload_to_s3(args.environment):
            sys.exit(1)
        
        print_step("Updating Lambda function code...")
        bucket_name = f"{PROJECT_NAME}-code-{ACCOUNT_ID}"
        success, output = run_command(
            f"aws lambda update-function-code "
            f"--function-name {PROJECT_NAME}-{args.environment} "
            f"--s3-bucket {bucket_name} "
            f"--s3-key lambda-code-{args.environment}.zip",
            shell=True
        )
        
        if success:
            print_success("Lambda function code updated")
        else:
            print_error(f"Failed to update function code: {output}")
            sys.exit(1)
    
    elif args.action == "test":
        # Test existing deployment
        success, output = run_command(
            f"aws cloudformation describe-stacks "
            f"--stack-name {PROJECT_NAME}-{args.environment} "
            f"--query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' "
            f"--output text "
            f"--region {REGION}",
            shell=True
        )
        
        if success and output.strip():
            api_endpoint = output.strip()
            test_api(api_endpoint)
        else:
            print_error(f"Stack not found: {PROJECT_NAME}-{args.environment}")
            sys.exit(1)
    
    print(f"\n{Colors.GREEN}✓ All done!{Colors.ENDC}\n")

if __name__ == "__main__":
    main()
