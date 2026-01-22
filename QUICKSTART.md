# NeurowellCA - Quick Start Guide

## 🚀 Start the Application (3 Steps)

### Step 1: Start Docker Services
```bash
cd "C:\Users\DELL\OneDrive\Desktop\4-2 Project\NeurowellCA"
docker-compose up -d postgres ollama qdrant
```

Wait 10 seconds for services to be healthy.

### Step 2: Ensure Ollama Model is Ready
```bash
docker exec -it neurowellca-ollama ollama pull llama3.2:3b
```

### Step 3: Start Backend
```bash
cd backend
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Wait for: `✅ Application started successfully`

---

## 🔗 Access Points

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Qdrant Dashboard**: http://localhost:6333/dashboard

---

## 🧪 Quick Test

### 1. Register a User
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/auth/register" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"username":"demo","email":"demo@test.com","password":"demo123","full_name":"Demo User","age":25}'
```

### 2. Login
```powershell
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"username":"demo","password":"demo123"}'
$token = $response.access_token
Write-Host "Token: $token"
```

### 3. Send Chat Message
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/chat/message" -Method POST -Headers @{"Content-Type"="application/json"; "Authorization"="Bearer $token"} -Body '{"message":"Hello, I need someone to talk to"}'
```

### 4. Get Chat History
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/chat/sessions" -Method GET -Headers @{"Authorization"="Bearer $token"}
```

---

## 📊 View Database

### Get Statistics
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/admin/stats" -Method GET -Headers @{"Authorization"="Bearer $token"}
```

### Get Users
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/admin/users?limit=10" -Method GET -Headers @{"Authorization"="Bearer $token"}
```

### Get Conversations
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/admin/conversations?limit=20" -Method GET -Headers @{"Authorization"="Bearer $token"}
```

---

## 🛑 Stop Services

### Stop Backend
Press `Ctrl+C` in the backend terminal

### Stop Docker
```bash
cd "C:\Users\DELL\OneDrive\Desktop\4-2 Project\NeurowellCA"
docker-compose down
```

---

## 🔧 Maintenance Commands

### Reset Database (Caution!)
```bash
docker exec -it neurowellca-postgres psql -U neurowellca_user -d neurowellca_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

### View Ollama Models
```bash
docker exec -it neurowellca-ollama ollama list
```

### Check Docker Status
```bash
docker-compose ps
```

### View Backend Logs
Backend logs appear in the terminal where you run uvicorn.

---

## ⚡ One-Command Startup Script

Save this as `start.bat`:
```batch
@echo off
echo Starting NeurowellCA...
cd /d "%~dp0"

echo [1/3] Starting Docker services...
docker-compose up -d postgres ollama qdrant

echo [2/3] Waiting for services...
timeout /t 10 /nobreak

echo [3/3] Starting backend...
cd backend
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Run: `start.bat`

---

## 📝 Important Notes

1. **Port 8000** must be free
2. **Docker Desktop** must be running
3. **Python 3.11+** required
4. First startup takes ~30 seconds (loading models)
5. Ollama model (llama3.2:3b) is ~2GB

---

## 🆘 Quick Fixes

### "Port 8000 already in use"
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
```

### "Docker not running"
Start Docker Desktop manually

### "Module not found"
```bash
cd backend
pip install -r requirements.txt
```

---

## 📞 Support

Check [README.md](README.md) for full documentation and troubleshooting.
