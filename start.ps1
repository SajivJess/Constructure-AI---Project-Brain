# Quick setup and run script - One command to start everything!

param(
    [switch]$SkipSetup
)

$ErrorActionPreference = "Stop"

Write-Host "`n=========================================================" -ForegroundColor Cyan
Write-Host "       CONSTRUCTURE AI - PROJECT BRAIN" -ForegroundColor Cyan
Write-Host "   Applied LLM Engineer Technical Assignment" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# Step 1: Check prerequisites
Write-Host "`n[1/6] Checking Prerequisites..." -ForegroundColor Yellow

$pythonOk = $false
$nodeOk = $false

try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK Python: $pythonVersion" -ForegroundColor Green
        $pythonOk = $true
    }
} catch {
    Write-Host "  ERROR Python not found" -ForegroundColor Red
}

try {
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK Node.js: $nodeVersion" -ForegroundColor Green
        $nodeOk = $true
    }
} catch {
    Write-Host "  ERROR Node.js not found" -ForegroundColor Red
}

if (-not $pythonOk -or -not $nodeOk) {
    Write-Host "`nERROR Missing prerequisites!" -ForegroundColor Red
    Write-Host "Please install:" -ForegroundColor Yellow
    if (-not $pythonOk) { Write-Host "  - Python 3.8+ from https://www.python.org/" }
    if (-not $nodeOk) { Write-Host "  - Node.js 16+ from https://nodejs.org/" }
    exit 1
}

# Step 2: Setup Backend
if (-not $SkipSetup -or -not (Test-Path "backend/venv")) {
    Write-Host "`n[2/6] Setting up Backend..." -ForegroundColor Yellow
    
    Push-Location backend
    
    if (-not (Test-Path "venv")) {
        Write-Host "  Creating virtual environment..." -ForegroundColor Gray
        python -m venv venv
    }
    
    Write-Host "  Activating virtual environment..." -ForegroundColor Gray
    & .\venv\Scripts\Activate.ps1
    
    Write-Host "  Installing dependencies..." -ForegroundColor Gray
    pip install -q -r requirements.txt
    
    if (-not (Test-Path ".env")) {
        Write-Host "  Creating .env file..." -ForegroundColor Gray
        Copy-Item .env.example .env
    }
    
    New-Item -ItemType Directory -Force -Path "data/uploads" | Out-Null
    New-Item -ItemType Directory -Force -Path "data/chroma_db" | Out-Null
    
    Write-Host "  OK Backend ready!" -ForegroundColor Green
    Pop-Location
} else {
    Write-Host "`n[2/6] Skipping backend setup..." -ForegroundColor Gray
}

# Step 3: Setup Frontend
if (-not $SkipSetup -or -not (Test-Path "frontend/node_modules")) {
    Write-Host "`n[3/6] Setting up Frontend..." -ForegroundColor Yellow
    
    Push-Location frontend
    
    Write-Host "  Installing dependencies..." -ForegroundColor Gray
    npm install --silent
    
    if (-not (Test-Path ".env.local")) {
        Write-Host "  Creating .env.local..." -ForegroundColor Gray
        Copy-Item .env.local.example .env.local
    }
    
    Write-Host "  OK Frontend ready!" -ForegroundColor Green
    Pop-Location
} else {
    Write-Host "`n[3/6] Skipping frontend setup..." -ForegroundColor Gray
}

# Step 4: Check API Key
Write-Host "`n[4/6] Checking Configuration..." -ForegroundColor Yellow

$envContent = Get-Content "backend/.env" -Raw
if ($envContent -match "OPENAI_API_KEY=sk-proj-") {
    Write-Host "  OK OpenAI API key configured" -ForegroundColor Green
} else {
    Write-Host "  WARNING OpenAI API key not set!" -ForegroundColor Red
    Write-Host "  Please edit backend/.env and add your OPENAI_API_KEY" -ForegroundColor Yellow
    Write-Host "  (You can do this later - basic features will still work)" -ForegroundColor Gray
}

# Step 5: Start Backend
Write-Host "`n[5/6] Starting Backend Server..." -ForegroundColor Yellow

$backendPath = Resolve-Path "backend"
$backendJob = Start-Job -ScriptBlock {
    param($path)
    Set-Location $path
    & .\venv\Scripts\Activate.ps1
    uvicorn main:app --reload --port 8000 2>&1
} -ArgumentList $backendPath

Write-Host "  Backend starting at http://localhost:8000" -ForegroundColor Green
Start-Sleep -Seconds 3

# Step 6: Start Frontend
Write-Host "`n[6/6] Starting Frontend Server..." -ForegroundColor Yellow

$frontendPath = Resolve-Path "frontend"
$frontendJob = Start-Job -ScriptBlock {
    param($path)
    Set-Location $path
    npm run dev 2>&1
} -ArgumentList $frontendPath

Write-Host "  Frontend starting at http://localhost:3000" -ForegroundColor Green

# Wait for servers to start
Write-Host "`nWaiting for servers to start..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Final message
Write-Host "`n=========================================================" -ForegroundColor Cyan
Write-Host "                 ALL SYSTEMS GO!" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "`nOpen your browser: http://localhost:3000`n" -ForegroundColor Green
Write-Host "Login credentials:" -ForegroundColor White
Write-Host "  Email: testingcheckuser1234@gmail.com" -ForegroundColor Gray
Write-Host "  Password: testpassword123`n" -ForegroundColor Gray
Write-Host "Quick Actions:" -ForegroundColor White
Write-Host "  1. Upload construction documents (PDFs)" -ForegroundColor Gray
Write-Host "  2. Ask: What is the fire rating for corridor partitions?" -ForegroundColor Gray
Write-Host "  3. Try: Generate a door schedule" -ForegroundColor Gray
Write-Host "  4. Test: List all rooms with their finishes`n" -ForegroundColor Gray
Write-Host "Documentation:" -ForegroundColor White
Write-Host "  - Quick Start: QUICK_START.md" -ForegroundColor Gray
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "  - Full Guide: README.md`n" -ForegroundColor Gray
Write-Host "To stop servers: Press Ctrl+C`n" -ForegroundColor Yellow
Write-Host "=========================================================" -ForegroundColor Cyan

# Keep script running and forward logs
try {
    while ($true) {
        $backendOutput = Receive-Job -Job $backendJob -Keep
        $frontendOutput = Receive-Job -Job $frontendJob -Keep
        
        if ($backendOutput) {
            Write-Host "[BACKEND] $backendOutput" -ForegroundColor Blue
        }
        if ($frontendOutput) {
            Write-Host "[FRONTEND] $frontendOutput" -ForegroundColor Magenta
        }
        
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "`nStopping servers..." -ForegroundColor Yellow
    Stop-Job -Job $backendJob, $frontendJob
    Remove-Job -Job $backendJob, $frontendJob
    Write-Host "Servers stopped" -ForegroundColor Green
}
