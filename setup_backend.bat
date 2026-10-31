@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "KAGGLE_CONFIG_DIR=%CD%\.kaggle"
set "KAGGLE_API_TOKEN=%CD%\.kaggle\access_token"
set "HF_HOME=%CD%\.cache\huggingface"
set "TRANSFORMERS_CACHE=%CD%\.cache\huggingface"
set "TORCH_HOME=%CD%\.cache\torch"
set "PIP_CACHE_DIR=%CD%\.cache\pip"
set "TEMP=%CD%\.cache\tmp"
set "TMP=%CD%\.cache\tmp"

if not exist "%CD%\.cache\pip" mkdir "%CD%\.cache\pip"
if not exist "%CD%\.cache\tmp" mkdir "%CD%\.cache\tmp"

where python >nul 2>nul
if errorlevel 1 (
    echo Khong tim thay Python trong PATH.
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" python -m venv .venv
if errorlevel 1 exit /b 1

".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
if errorlevel 1 exit /b 1

set "PYTHONPATH=%CD%"
".venv\Scripts\python.exe" -m backend.migrations.runner
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" backend\scripts\download_model.py
if errorlevel 1 exit /b 1

echo Backend da san sang. Chay run_backend.bat de khoi dong API.
