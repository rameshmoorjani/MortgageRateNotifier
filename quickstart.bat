@echo off
REM Quick Start Script for Production Deployment (Windows)
REM Usage: quickstart.bat

setlocal enabledelayedexpansion

echo.
echo ================================================================================
echo MORTGAGE RATE NOTIFIER - PRODUCTION QUICK START (WINDOWS)
echo ================================================================================
echo.

REM Check Python
echo [STEP 1] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    exit /b 1
)
for /f "tokens=*" %%A in ('python --version') do set PYTHON_VERSION=%%A
echo [OK] %PYTHON_VERSION%

REM Create virtual environment
echo.
echo [STEP 2] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment exists
)

REM Activate virtual environment
echo.
echo [STEP 3] Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated

REM Install dependencies
echo.
echo [STEP 4] Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    exit /b 1
)
echo [OK] Dependencies installed

REM Create logs directory
echo.
echo [STEP 5] Creating logs directory...
if not exist "logs" (
    mkdir logs
)
echo [OK] Logs directory ready

REM Check .env
echo.
echo [STEP 6] Checking environment configuration...
if not exist ".env" (
    echo [WARNING] .env file not found
    echo Create .env with at minimum:
    echo   OPENAI_API_KEY=your-api-key-here
    echo.
) else (
    findstr /M "OPENAI_API_KEY" .env >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] OPENAI_API_KEY not found in .env
        exit /b 1
    ) else (
        echo [OK] .env file configured
    )
)

REM Check users.json
echo.
echo [STEP 7] Checking user data...
if not exist "users.json" (
    echo [WARNING] users.json not found
    echo Create users.json with your user list
) else (
    echo [OK] users.json found
)

REM Run tests
echo.
echo [STEP 8] Running validation tests...
python test_rag_system.py >nul 2>&1
if errorlevel 1 (
    echo [WARNING] RAG system test failed - check OPENAI_API_KEY
) else (
    echo [OK] RAG system test passed
)

python test_rag_batch.py >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Batch processing test failed
) else (
    echo [OK] Batch processing test passed
)

REM Summary
echo.
echo ================================================================================
echo QUICK START COMPLETE
echo ================================================================================
echo.
echo Next steps:
echo   1. Configure environment (if needed): notepad .env
echo   2. Prepare users: notepad users.json
echo   3. Test run: python start_production.py --mode once --users users.json
echo   4. Daily schedule: python start_production.py --mode daily --users users.json
echo.
echo For help: python start_production.py --help
echo For detailed guide: see PRODUCTION_DEPLOYMENT.md
echo.
pause
