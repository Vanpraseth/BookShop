@echo off

if "%PORT%"=="" set PORT=5001

cd backend
call venv\Scripts\activate
start "BookShop" cmd /k python server.py
timeout /t 2 >nul
start http://localhost:%PORT%/
