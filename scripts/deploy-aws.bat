@echo off
REM 🚀 Mortgage Rate Notifier - AWS Deployment Helper
REM This batch file helps you install Docker and prepare for AWS deployment

echo.
echo ========================================
echo Mortgage Rate Notifier - AWS Setup
echo ========================================
echo.

REM Check if Docker is installed
echo Checking Docker installation...
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Docker is already installed
    docker --version
) else (
    echo ✗ Docker is not installed
    echo.
    echo Options:
    echo 1. Download from: https://www.docker.com/products/docker-desktop
    echo 2. Or install via Chocolatey:
    echo    choco install docker-desktop -y
    echo.
    pause
)

REM Check AWS CLI
echo.
echo Checking AWS CLI installation...
aws --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ AWS CLI is installed
    aws --version
) else (
    echo ✗ AWS CLI is not installed
    echo Download from: https://aws.amazon.com/cli/
    pause
)

REM Check credentials
echo.
echo Checking AWS credentials...
aws sts get-caller-identity >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ AWS credentials are configured
    aws sts get-caller-identity
) else (
    echo ✗ AWS credentials not found
    echo Run: aws configure
    pause
)

echo.
echo ========================================
echo To deploy your application:
echo ========================================
echo.
echo Option 1: Run the PowerShell script
echo   .\deploy-aws.ps1 -Step full
echo.
echo Option 2: Manual steps
echo   1. Install Docker (if not already installed)
echo   2. Run: aws configure
echo   3. Run: .\deploy-aws.ps1 -Step full
echo.
pause
