@echo off
setlocal
cd /d "%~dp0"

set "BOOTSTRAP_PYTHON="
where py >nul 2>nul
if not errorlevel 1 set "BOOTSTRAP_PYTHON=py -3"
if "%BOOTSTRAP_PYTHON%"=="" (
    where python >nul 2>nul
    if not errorlevel 1 set "BOOTSTRAP_PYTHON=python"
)
if "%BOOTSTRAP_PYTHON%"=="" (
    echo Failed to find Python. Install Python 3 first.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    %BOOTSTRAP_PYTHON% -m venv .venv
    if errorlevel 1 (
        echo Failed to create .venv. Install Python 3 and ensure venv is available.
        pause
        exit /b 1
    )
)

.venv\Scripts\python.exe -m pip install -U pip
if errorlevel 1 (
    echo Failed to upgrade pip inside project .venv.
    pause
    exit /b 1
)

.venv\Scripts\python.exe -m pip install -r requirements-windows.txt
if errorlevel 1 (
    echo Failed to install Windows requirements inside project .venv.
    pause
    exit /b 1
)

echo Project .venv is ready.
echo Run: run_gui_windows.bat
pause
