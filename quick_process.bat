@echo off
REM ========================================
REM BGRemover - Procesamiento Rapido
REM Procesa todas las imagenes con la configuracion optima
REM ========================================

call .venv\Scripts\activate.bat
bgremover input_folder/ output_folder/ --batch --threshold 20

echo.
echo ✅ Procesamiento completado!
pause