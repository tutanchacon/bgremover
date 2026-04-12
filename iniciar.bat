@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set "SCRIPT_DIR=%~dp0"
"%SCRIPT_DIR%venv\Scripts\python.exe" "%SCRIPT_DIR%gui.py"
