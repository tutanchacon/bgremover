@echo off
REM ========================================
REM BGRemover - Procesamiento por Lotes
REM ========================================
echo 🎨 BGRemover - Procesamiento Automatico
echo =======================================

REM Activar entorno virtual
echo 📋 Activando entorno virtual...
call .venv\Scripts\activate.bat

REM Verificar que las carpetas existen
if not exist "input_folder" (
    echo ❌ Error: No existe la carpeta input_folder
    echo 💡 Crea la carpeta input_folder y coloca tus imagenes ahi
    pause
    exit /b 1
)

REM Crear carpeta de salida si no existe
if not exist "output_folder" (
    echo 📁 Creando carpeta output_folder...
    mkdir output_folder
)

REM Contar imagenes en input_folder
echo 🔍 Verificando imagenes en input_folder...
set /a count=0
for %%f in (input_folder\*.jpg input_folder\*.jpeg input_folder\*.png input_folder\*.bmp input_folder\*.tiff) do (
    if exist "%%f" set /a count+=1
)

if %count%==0 (
    echo ❌ No se encontraron imagenes en input_folder
    echo 💡 Formatos soportados: JPG, JPEG, PNG, BMP, TIFF
    pause
    exit /b 1
)

echo ✅ Encontradas %count% imagenes para procesar
echo.

REM Procesar imagenes
echo 🚀 Iniciando procesamiento con configuracion optima...
echo ⚙️  Configuracion: Umbral 20 (preserva todos los elementos)
echo.

bgremover input_folder/ output_folder/ --batch --threshold 20 --verbose

REM Verificar resultado
if %errorlevel%==0 (
    echo.
    echo ✅ ¡Procesamiento completado exitosamente!
    echo 📁 Revisa la carpeta output_folder para ver los resultados
    echo 🎯 Todos los elementos del personaje han sido preservados
) else (
    echo.
    echo ❌ Error durante el procesamiento
    echo 💡 Verifica que las imagenes sean validas
)

echo.
echo Presiona cualquier tecla para cerrar...
pause >nul