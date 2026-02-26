@echo off
REM Quick Start Script for NeurowellCA Development

echo ================================================
echo NeurowellCA - Quick Development Start
echo ================================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker Desktop is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Step 1: Starting Docker services (DB, Vector DB, AI)...
docker-compose up -d postgres qdrant ollama backend

echo.
echo Step 2: Waiting for services to initialize...
timeout /t 15 /nobreak >nul

echo.
echo Step 3: Pulling Ollama AI model (first time only)...
docker exec neurowellca-ollama ollama pull llama3.2:3b

echo.
echo ================================================
echo ✅ Backend services ready!
echo ================================================
echo.
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Qdrant Dashboard: http://localhost:6333/dashboard
echo.
echo ================================================
echo Starting Frontend (Next.js)...
echo ================================================
echo.

cd frontend
start cmd /k "npm run dev"

echo.
echo Frontend will open in a new window...
echo Frontend URL: http://localhost:3000 (or 3001 if 3000 is busy)
echo.
echo ================================================
echo 🎉 All services started!
echo ================================================
echo.
echo To stop services:
echo   docker-compose down
echo.
pause
