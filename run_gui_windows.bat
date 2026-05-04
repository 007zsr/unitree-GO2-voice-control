@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Project virtual environment .venv was not found.
    echo Please run setup_windows_venv.bat first.
    pause
    exit /b 1
)

.venv\Scripts\python.exe scripts\run\run_gui.py
pause
