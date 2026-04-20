@echo off
chcp 65001 > nul
call .venv\Scripts\activate.bat

echo.
echo  BGRemover - Servidor HTTP
echo  =========================
echo  1. Desarrollo  (localhost:5000, debug + auto-reload)
echo  2. Local       (localhost:5000, estable, sin debug)
echo  3. Red local   (0.0.0.0:5000,  accesible desde otras PCs)
echo  4. Produccion  (localhost:5000, Waitress multi-hilo)
echo.
set /p OPCION="  Selecciona modo [1-4, Enter=2]: "

if "%OPCION%"=="1" (
    python bgremover_server.py --mode dev
) else if "%OPCION%"=="3" (
    python bgremover_server.py --mode local --host 0.0.0.0
) else if "%OPCION%"=="4" (
    python bgremover_server.py --mode prod
) else (
    python bgremover_server.py --mode local
)
