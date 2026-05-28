@echo off
title Travel Bookmark Demo

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo ============================================
echo   Travel Bookmark Demo (SQLite)
echo ============================================

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

:: Build virtual environment
if not exist "%ROOT%venv\Scripts\python.exe" (
    echo [1/4] Creating Python venv...
    python -m venv "%ROOT%venv"
)

call "%ROOT%venv\Scripts\activate.bat"

echo [1/4] Installing Python packages...
pip install fastapi uvicorn "python-jose[cryptography]" bcrypt pydantic -q

:: Init DB
if not exist "%ROOT%data.db" (
    echo [2/4] Importing data, please wait...
    python "%ROOT%data\import_data.py"
) else (
    echo [2/4] Database already exists, skip import
)

:: NPM install
if not exist "%ROOT%node_modules" (
    echo [3/4] Installing frontend packages...
    call npm install --prefix "%ROOT%"
) else (
    echo [3/4] Frontend packages ready
)

echo [4/4] Starting servers...
echo.
echo   Backend  : http://localhost:8000
echo   API Docs : http://localhost:8000/api/docs
echo   Frontend : http://localhost:5173
echo.
echo ============================================

start "Backend" cmd /c "cd /d %ROOT% && call venv\Scripts\activate.bat && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

start "Frontend" cmd /c "cd /d %ROOT% && npm run dev"

echo Servers started! Open http://localhost:5173 in your browser.
echo Close this window or press Ctrl+C to stop.
pause
