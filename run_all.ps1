# Run both Backend and Frontend in separate windows
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting Alzheimer MRI Staging (Backend + Frontend)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot'; .\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot\frontend'; npm run dev"

Write-Host "`nServers launched in separate windows:" -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000 (API Docs: http://localhost:8000/docs)" -ForegroundColor Yellow
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
