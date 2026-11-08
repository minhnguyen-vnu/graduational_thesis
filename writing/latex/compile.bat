@echo off
set "PATH=C:\Users\ADMIN\AppData\Local\Programs\MiKTeX\miktex\bin\x64;%PATH%"
set "PYTHON_EXE=C:\New folder\python-3.11.9\tools\python.exe"

echo [0/3] Kiem tra van phong hoc thuat va giong van AI (Audit Gate)...
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" ..\scripts\audit_thesis.py chapters\chapter4.tex --strict
    if errorlevel 1 (
        echo.
        echo ============================================================
        echo [THAT BAI] Phat hien vi pham van phong hoac giong van AI!
        echo Vui long sua cac vi pham tren truoc khi bien dich PDF.
        echo ============================================================
        pause
        exit /b 1
    )
)

echo [1/3] Running pdfLaTeX (Luot 1)...
pdflatex -interaction=nonstopmode main.tex > nul
echo [2/3] Resolving Citations (BibTeX)...
bibtex main > nul
echo [3/3] Finalizing Cross-references and Table of Contents...
pdflatex -interaction=nonstopmode main.tex > nul
pdflatex -interaction=nonstopmode main.tex
echo.
echo ============================================================
echo   Bien dich thanh cong! File PDF: main.pdf
echo ============================================================
pause
