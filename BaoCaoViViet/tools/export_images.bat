@echo off
setlocal
cd /d "%~dp0\.."

set "PYTHON_EXE=D:\appfood4\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
  echo Khong tim thay Python tai %PYTHON_EXE%
  exit /b 2
)

"%PYTHON_EXE%" tools\export_report_images.py --report "%CD%" --output "D:\BaoCaoViViet-HinhAnh"
if errorlevel 1 exit /b 1
echo Da xuat bo hinh vao D:\BaoCaoViViet-HinhAnh
endlocal
