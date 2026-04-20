@echo off
REM ========================================
REM BGRemover - Procesamiento Recursivo
REM Procesa todas las imágenes manteniendo la estructura de directorios
REM ========================================
echo 🎨 BGRemover - Procesamiento Recursivo con Estructura
echo ====================================================

REM Activar entorno virtual
echo 📋 Activando entorno virtual...
call .venv\Scripts\activate.bat

REM Verificar que las carpetas existen
if not exist "input_folder" (
    echo ❌ Error: No existe la carpeta input_folder
    echo 💡 Crea la carpeta input_folder y coloca tus imagenes (con subdirectorios si quieres)
    pause
    exit /b 1
)

REM Crear carpeta de salida si no existe
if not exist "output_folder" (
    echo 📁 Creando carpeta output_folder...
    mkdir output_folder
)

REM Contar imagenes recursivamente en todos los subdirectorios
echo 🔍 Escaneando directorios recursivamente...
set /a count=0
for /r "input_folder" %%f in (*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp) do (
    if exist "%%f" set /a count+=1
)

if %count%==0 (
    echo ❌ No se encontraron imagenes en input_folder ni sus subdirectorios
    echo 💡 Formatos soportados: JPG, JPEG, PNG, BMP, TIFF, WEBP
    echo 📂 Verifica que haya imagenes en input_folder o cualquier subcarpeta
    pause
    exit /b 1
)

echo ✅ Encontradas %count% imagenes en total (incluyendo subdirectorios)
echo ⚙️  Configuracion: Umbral 20 + Recursivo (mantiene estructura)
echo 📂 Procesará TODOS los subdirectorios de input_folder
echo.

REM Usar el script Python para procesamiento recursivo
echo 🚀 Iniciando procesamiento recursivo...
python process_recursive.py input_folder output_folder 20 true

REM Verificar resultado
if %errorlevel%==0 (
    echo.
    echo ✅ ¡Procesamiento recursivo completado exitosamente!
    echo 📁 Revisa la carpeta output_folder 
    echo 🗂️  La estructura de directorios se ha mantenido
    echo 🎯 Todos los elementos del personaje preservados
) else (
    echo.
    echo ❌ Error durante el procesamiento
    echo 💡 Verifica que las imagenes sean validas
)

echo.
echo Presiona cualquier tecla para cerrar...
pause >nul