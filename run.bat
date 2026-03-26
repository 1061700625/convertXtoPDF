@echo off
chcp 65001 >nul
title EPUB/MOBI to PDF Converter

echo ============================================================
echo EPUB/MOBI to PDF Converter
echo ============================================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\python.exe" (
    echo [OK] Virtual environment found.
    echo.
    echo [INFO] Starting application...
    echo.
    
    REM Run application in desktop mode
    venv\Scripts\python app.py --mode desktop
    
    goto end
)

echo [INFO] Virtual environment not found.
echo [INFO] First-time setup required...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.8+ from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Create virtual environment
echo [INFO] Creating virtual environment...
python -m venv venv

echo [INFO] Installing dependencies...
echo This may take 2-3 minutes...
echo.
venv\Scripts\pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies!
    echo Please check your network connection and try again.
    pause
    exit /b 1
)

echo.
echo [OK] Dependencies installed successfully!
echo.
echo ============================================================
echo [INFO] First-time setup complete!
echo ============================================================
echo.
echo Next time, the application will start directly.
echo.
pause

echo [INFO] Starting application...
echo.

REM Run application in desktop mode
venv\Scripts\python app.py --mode desktop

:end
pause
