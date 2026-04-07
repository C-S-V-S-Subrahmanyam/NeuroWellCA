@echo off
echo ================================================
echo Starting NeurowellCA Services (Docker)
echo ================================================
echo.
echo This will start:
echo - PostgreSQL (Database)
echo - Qdrant (Vector Database)
echo - Ollama (AI LLM)
echo - FastAPI Backend
echo.
echo Frontend runs separately with: npm run dev
echo ================================================
echo.

echo Cleaning up old containers...
docker-compose down -v 2>nul

echo.
echo Starting services with Docker Compose...
docker-compose up -d postgres qdrant ollama

echo.
echo Waiting for databases to be ready (15 seconds)...
timeout /t 15 /nobreak >nul

echo.
echo Starting backend...
docker-compose up -d backend

echo.
echo Waiting for backend to start (10 seconds)...
timeout /t 10 /nobreak >nul

echo.
echo Pulling Ollama model (llama3.2:3b - first time only, ~2 minutes)...
docker exec neurowellca-ollama ollama pull llama3.2:3b

echo.
echo ================================================
echo ✅ Docker services started!
echo ================================================
echo.
echo Services:
docker-compose ps
echo.
echo Access Points:
echo - Backend API: http://localhost:8000
echo - API Docs: http://localhost:8000/docs
echo - Qdrant Dashboard: http://localhost:6333/dashboard
echo.
echo To start frontend (in separate terminal):
echo   cd frontend
echo   npm run dev
echo.
echo Frontend will run on: http://localhost:3000 or 3001
echo ================================================
pause
