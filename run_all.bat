@echo off
echo ========================================================
echo Starting Alzheimer MRI Staging (Backend + Frontend)
echo ========================================================

start "Backend Server (FastAPI)" cmd /k "cd /d %~dp0 && .venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
start "Frontend Server (Vite React)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Both servers have been launched in separate windows!
echo - Backend:  http://localhost:8000 (Docs: http://localhost:8000/docs)
echo - Frontend: http://localhost:5173
echo ========================================================
pause
