@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "HF_HOME=%CD%\.cache\huggingface"
set "TRANSFORMERS_CACHE=%CD%\.cache\huggingface"
set "TORCH_HOME=%CD%\.cache\torch"
set "TEMP=%CD%\.cache\tmp"
set "TMP=%CD%\.cache\tmp"

if not exist ".venv\Scripts\python.exe" (
    echo Chua co moi truong backend. Hay chay setup_backend.bat truoc.
    exit /b 1
)

set "PYTHONPATH=%CD%"
".venv\Scripts\python.exe" -m backend.migrations.runner
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
