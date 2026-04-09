@echo off
chcp 65001 >nul
setlocal

REM Verifico que se pasaron los argumentos necesarios
if "%~1"=="" (
    echo Uso: procesaImagen.bat entrada.png salida.png [verbose]
    echo.
    echo Ejemplos:
    echo   procesaImagen.bat foto.jpg resultado.png
    echo   procesaImagen.bat avatar.webp limpio.png true
    exit /b 1
)

if "%~2"=="" (
    echo Error: Falta el nombre del archivo de salida
    echo Uso: procesaImagen.bat entrada.png salida.png [verbose]
    exit /b 1
)

REM Obtengo el directorio donde esta el script
set "SCRIPT_DIR=%~dp0"

REM Configuro encoding UTF-8 para emojis
set PYTHONIOENCODING=utf-8

REM Ejecuto el script Python con el venv
"%SCRIPT_DIR%venv\Scripts\python.exe" "%SCRIPT_DIR%bgremover.py" %*

endlocal
