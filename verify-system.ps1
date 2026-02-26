#!/usr/bin/env pwsh
# System Verification Script for NeurowellCA
# Run this to verify backend-frontend integration

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   NeurowellCA System Verification" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Check Docker Services
Write-Host "1. Checking Docker Services..." -ForegroundColor Yellow
$containers = docker ps --format "{{.Names}}\t{{.Status}}" | findstr "neurowellca"
if ($containers) {
    Write-Host "   ✅ All containers running" -ForegroundColor Green
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | findstr "neurowellca"
} else {
    Write-Host "   ❌ Docker containers not running!" -ForegroundColor Red
    Write-Host "   Run: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

# 2. Check Backend Health
Write-Host "`n2. Checking Backend Health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -UseBasicParsing
    Write-Host "   ✅ Backend: $($health.status) - v$($health.version)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Backend not responding!" -ForegroundColor Red
    exit 1
}

# 3. Check Database Connection
Write-Host "`n3. Checking Database..." -ForegroundColor Yellow
try {
    $userCount = docker exec neurowellca-postgres psql -U neurowellca_user -d neurowellca_db -t -c "SELECT COUNT(*) FROM users;" 2>$null
    $chatCount = docker exec neurowellca-postgres psql -U neurowellca_user -d neurowellca_db -t -c "SELECT COUNT(*) FROM conversations;" 2>$null
    $assessmentCount = docker exec neurowellca-postgres psql -U neurowellca_user -d neurowellca_db -t -c "SELECT COUNT(*) FROM assessments;" 2>$null
    
    Write-Host "   ✅ Database connected" -ForegroundColor Green
    Write-Host "      - Users: $($userCount.Trim())" -ForegroundColor Cyan
    Write-Host "      - Conversations: $($chatCount.Trim())" -ForegroundColor Cyan
    Write-Host "      - Assessments: $($assessmentCount.Trim())" -ForegroundColor Cyan
} catch {
    Write-Host "   ❌ Database connection failed!" -ForegroundColor Red
    exit 1
}

# 4. Check Ollama Model
Write-Host "`n4. Checking Ollama AI Model..." -ForegroundColor Yellow
try {
    $models = docker exec neurowellca-ollama ollama list 2>$null | Select-String "llama3.2:3b"
    if ($models) {
        Write-Host "   ✅ Ollama model installed: llama3.2:3b" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Ollama model not found!" -ForegroundColor Red
        Write-Host "   Run: docker exec neurowellca-ollama ollama pull llama3.2:3b" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️  Could not check Ollama" -ForegroundColor Yellow
}

# 5. Check Frontend
Write-Host "`n5. Checking Frontend..." -ForegroundColor Yellow
$frontend3000 = Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($frontend3000) {
    Write-Host "   ✅ Frontend running on http://localhost:3000" -ForegroundColor Green
} else {
    Write-Host "   ❌ Frontend not running!" -ForegroundColor Red
    Write-Host "   Run: cd frontend && npm run dev" -ForegroundColor Yellow
}

# 6. Test Backend API
Write-Host "`n6. Testing Backend API..." -ForegroundColor Yellow
Write-Host "   Testing login with admin account..." -ForegroundColor Cyan

try {
    $loginBody = @{
        username = "admin"
        password = "admin"
    } | ConvertTo-Json -Compress
    
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
    
    if ($loginResponse.access_token) {
        Write-Host "   ✅ Login successful!" -ForegroundColor Green
        Write-Host "   Token: $($loginResponse.access_token.Substring(0,30))..." -ForegroundColor DarkGray
        
        # Test fetching data with token
        $headers = @{
            Authorization = "Bearer $($loginResponse.access_token)"
        }
        
        Write-Host "`n   Testing data retrieval..." -ForegroundColor Cyan
        
        try {
            $sessions = Invoke-RestMethod -Uri "http://localhost:8000/api/chat/sessions" -Headers $headers
            Write-Host "   ✅ Chat API working - Sessions: $($sessions.Count)" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️  Chat sessions: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        
        try {
            $assessments = Invoke-RestMethod -Uri "http://localhost:8000/api/assessments/history" -Headers $headers
            Write-Host "   ✅ Assessment API working - Count: $($assessments.Count)" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️  Assessments: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        
    } else {
        Write-Host "   ❌ Login failed - no token received" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ API test failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 7. Show Available Users
Write-Host "`n7. Available Users for Testing:" -ForegroundColor Yellow
docker exec neurowellca-postgres psql -U neurowellca_user -d neurowellca_db -c "SELECT id, username, email FROM users;" 2>$null | Select-Object -Skip 2

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   Verification Complete!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "📌 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Open browser: http://localhost:3000" -ForegroundColor White
Write-Host "   2. Login with one of the users above" -ForegroundColor White
Write-Host "   3. Try sending a chat message" -ForegroundColor White
Write-Host "   4. Check browser console (F12) for errors" -ForegroundColor White
Write-Host ""

Write-Host "📊 View Backend Logs:" -ForegroundColor Yellow
Write-Host "   docker logs neurowellca-backend -f --tail 50" -ForegroundColor White
Write-Host ""

Write-Host "🔍 For detailed diagnostic info, see:" -ForegroundColor Yellow
Write-Host "   SYSTEM_DIAGNOSTIC.md" -ForegroundColor White
Write-Host ""
