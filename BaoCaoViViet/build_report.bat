@echo off
setlocal
cd /d "%~dp0"

where xelatex >nul 2>nul
if errorlevel 1 (
  echo Khong tim thay xelatex. Hay cai MiKTeX va mo lai terminal.
  exit /b 2
)

xelatex -disable-installer -interaction=nonstopmode -halt-on-error do-an.tex || exit /b 1
bibtex -disable-installer do-an || exit /b 1
xelatex -disable-installer -interaction=nonstopmode -halt-on-error do-an.tex || exit /b 1
xelatex -disable-installer -interaction=nonstopmode -halt-on-error do-an.tex || exit /b 1
copy /y do-an.pdf BaoCao-DoAn-ViViet.pdf >nul
echo Da tao BaoCao-DoAn-ViViet.pdf
endlocal
