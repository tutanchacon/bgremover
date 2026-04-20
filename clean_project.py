#!/usr/bin/env python3
"""
Limpieza del Proyecto Background Remover
========================================

Script para mantener el proyecto limpio y organizado.
Elimina archivos temporales, cachés y archivos de prueba innecesarios.

Uso:
    python clean_project.py
"""

import os
import shutil
import glob
import sys


def clean_project():
    """Limpia archivos temporales y innecesarios del proyecto."""
    
    print("🧹 Limpieza del Proyecto Background Remover")
    print("=" * 45)
    
    # Directorio base del proyecto
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Archivos y directorios a limpiar
    cleanup_patterns = [
        "__pycache__",
        "*.pyc",
        "*.pyo", 
        "*.pyd",
        ".pytest_cache",
        "*.egg-info",
        ".DS_Store",
        "Thumbs.db",
        "*.tmp",
        "*.temp"
    ]
    
    # Archivos de resultados temporales (mantener solo resultado_final.png)
    temp_results = [
        "modelo_*.png",
        "resultado_*.png",
        "comparacion_*.png", 
        "analisis_*.png",
        "limpia*.png"
    ]
    
    cleaned_count = 0
    
    # Limpiar patrones generales
    print("🔍 Buscando archivos temporales...")
    for pattern in cleanup_patterns:
        matches = glob.glob(os.path.join(project_dir, "**", pattern), recursive=True)
        for match in matches:
            try:
                if os.path.isdir(match):
                    shutil.rmtree(match)
                    print(f"   📁 Eliminado directorio: {os.path.basename(match)}")
                else:
                    os.remove(match)
                    print(f"   📄 Eliminado archivo: {os.path.basename(match)}")
                cleaned_count += 1
            except Exception as e:
                print(f"   ⚠️ No se pudo eliminar {match}: {e}")
    
    # Limpiar resultados temporales (excepto resultado_final.png)
    print("\n🖼️ Limpiando imágenes de resultado temporales...")
    for pattern in temp_results:
        matches = glob.glob(os.path.join(project_dir, pattern))
        for match in matches:
            # No eliminar resultado_final.png
            if not match.endswith("resultado_final.png"):
                try:
                    os.remove(match)
                    print(f"   🗑️ Eliminado: {os.path.basename(match)}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"   ⚠️ No se pudo eliminar {match}: {e}")
    
    # Verificar espacio liberado
    print(f"\n✅ Limpieza completada!")
    print(f"📊 Archivos eliminados: {cleaned_count}")
    
    # Mostrar estructura final
    print("\n📁 Estructura actual del proyecto:")
    show_project_structure(project_dir)


def show_project_structure(project_dir):
    """Muestra la estructura actual del proyecto."""
    
    ignore_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv'}
    ignore_files = {'*.pyc', '*.pyo', '*.pyd'}
    
    for root, dirs, files in os.walk(project_dir):
        # Filtrar directorios ignorados
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        level = root.replace(project_dir, '').count(os.sep)
        indent = '  ' * level
        folder_name = os.path.basename(root)
        
        if level == 0:
            print(f"{indent}bgremover/")
        else:
            print(f"{indent}├── {folder_name}/")
        
        # Mostrar archivos
        sub_indent = '  ' * (level + 1)
        for file in files:
            if not any(file.endswith(ext.replace('*', '')) for ext in ignore_files):
                print(f"{sub_indent}├── {file}")


def main():
    """Función principal."""
    
    print("🎨 ¿Deseas limpiar el proyecto Background Remover?")
    print("   Esto eliminará archivos temporales y resultados de prueba.")
    print("   (Se mantendrán: input.png, input2.png, resultado_final.png)")
    
    response = input("\n¿Continuar? (s/n): ").lower().strip()
    
    if response in ['s', 'si', 'y', 'yes']:
        clean_project()
    else:
        print("❌ Limpieza cancelada.")


if __name__ == "__main__":
    main()
