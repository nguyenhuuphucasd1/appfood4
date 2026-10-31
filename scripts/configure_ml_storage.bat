@echo off
setlocal
cd /d "%~dp0.."
set "KAGGLE_CONFIG_DIR=%CD%\.kaggle"
set "KAGGLE_API_TOKEN=%CD%\.kaggle\access_token"
set "HF_HOME=%CD%\.cache\huggingface"
set "TRANSFORMERS_CACHE=%CD%\.cache\huggingface"
set "TORCH_HOME=%CD%\.cache\torch"
set "PIP_CACHE_DIR=%CD%\.cache\pip"
set "TEMP=%CD%\.cache\tmp"
set "TMP=%CD%\.cache\tmp"
if not exist "%KAGGLE_CONFIG_DIR%" mkdir "%KAGGLE_CONFIG_DIR%"
if not exist "%HF_HOME%" mkdir "%HF_HOME%"
if not exist "%TORCH_HOME%" mkdir "%TORCH_HOME%"
if not exist "%PIP_CACHE_DIR%" mkdir "%PIP_CACHE_DIR%"
if not exist "%TEMP%" mkdir "%TEMP%"
echo Cau hinh ML da tro den o D: %CD%
