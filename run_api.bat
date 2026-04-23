@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Create venv: py -3.13 -m venv .venv
  echo Then: .venv\Scripts\pip install -r requirements.txt
  exit /b 1
)
".venv\Scripts\python.exe" -m uvicorn api_server:app --host 127.0.0.1 --port 8080
