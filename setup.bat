@echo off
REM NeuroWell-CA Setup Script for Windows
REM This script automates the setup process

echo ===================================
echo NeuroWell-CA Setup Script
echo ===================================
echo.

REM Check if Docker is installed
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo X Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)
echo [OK] Docker is installed

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo X Python is not installed. Please install Python 3.10 or higher.
    exit /b 1
)
echo [OK] Python is installed

REM Create .env file from example
echo.
echo Step 1: Setting up environment variables...
if not exist "backend\.env" (
    copy "backend\.env.example" "backend\.env" >nul
    echo [OK] Created backend\.env file
    echo [!] Please edit backend\.env and add your credentials (Twilio, JWT secret, etc.)
) else (
    echo [i] backend\.env already exists
)

REM Start Docker containers
echo.
echo Step 2: Starting Docker containers...
docker-compose up -d

echo [~] Waiting for containers to start (30 seconds)...
timeout /t 30 /nobreak >nul

REM Check if containers are running
docker ps | findstr "neurowellca-postgres" >nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] PostgreSQL container is running
) else (
    echo [X] PostgreSQL container failed to start
    exit /b 1
)

docker ps | findstr "neurowellca-ollama" >nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Ollama container is running
) else (
    echo [X] Ollama container failed to start
    exit /b 1
)

REM Pull Ollama model
echo.
echo Step 3: Pulling Ollama model (Llama 3.2 3B - 2GB download)...
docker exec neurowellca-ollama ollama pull llama3.2:latest

REM Set up Python virtual environment
echo.
echo Step 4: Setting up Python virtual environment...
cd backend

if not exist "venv" (
    python -m venv venv
    echo [OK] Created virtual environment
) else (
    echo [i] Virtual environment already exists
)

REM Activate virtual environment and install dependencies
echo.
echo Step 5: Installing Python dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

REM Initialize database
echo.
echo Step 6: Initializing database...
set FLASK_APP=run.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

echo.
echo ===================================
echo [OK] Setup Complete!
echo ===================================
echo.
echo Next steps:
echo 1. Edit backend\.env and add your Twilio credentials
echo 2. Start the backend:
echo    cd backend
echo    venv\Scripts\activate
echo    python run.py
echo 3. Open frontend\index.html in your browser
echo.
echo Docker services:
echo - PostgreSQL: http://localhost:5432
echo - Ollama: http://localhost:11434
echo.
echo Backend API: http://localhost:5000
echo.
pause
