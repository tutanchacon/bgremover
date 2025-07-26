#!/usr/bin/env python3
"""
Ajuste fino de bordes - Toma un resultado ya bueno y elimina solo píxeles de borde específicos
Diseñado para refinar resultados existentes, no empezar desde cero
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image

def analyze_border_pixels(original_image, mask, analysis_width=8):
    """
    Analiza los píxeles específicos del borde para encontrar blancos residuales
    """
    img_array = np.array(original_image)
    
    # 1. Encontrar el contorno exacto de la máscara actual
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    
    if not contours:
        return mask
    
    # 2. Crear máscara de banda de análisis muy específica
    # Erosionar la máscara para crear banda interior
    kernel = np.ones((analysis_width, analysis_width), np.uint8)
    inner_mask = cv2.erode(mask, kernel, iterations=1)
    
    # La banda de análisis son solo los píxeles del borde exterior
    border_band = cv2.subtract(mask, inner_mask)
    
    # 3. Análisis píxel por píxel en la banda
    result_mask = mask.copy()
    
    # Obtener coordenadas de los píxeles en la banda de borde
    border_coords = np.where(border_band > 0)
    
    print(f"🔍 Analizando {len(border_coords[0])} píxeles en banda de borde...")
    
    # 4. Para cada píxel en el borde, verificar si es blanco residual
    removed_count = 0
    
    for i in range(len(border_coords[0])):
        y, x = border_coords[0][i], border_coords[1][i]
        
        # Obtener valor RGB del píxel
        rgb_pixel = img_array[y, x]
        
        # Verificar múltiples criterios para píxel blanco residual
        is_white_residual = False
        
        # Criterio 1: RGB alto (muy blanco)
        if np.all(rgb_pixel > 240):
            is_white_residual = True
        
        # Criterio 2: Diferencia mínima entre canales (gris/blanco)
        elif np.max(rgb_pixel) - np.min(rgb_pixel) < 15 and np.mean(rgb_pixel) > 230:
            is_white_residual = True
        
        # Criterio 3: Análisis del entorno (si está rodeado de blancos)
        elif np.mean(rgb_pixel) > 225:
            # Verificar entorno 3x3
            y_start, y_end = max(0, y-1), min(img_array.shape[0], y+2)
            x_start, x_end = max(0, x-1), min(img_array.shape[1], x+2)
            neighborhood = img_array[y_start:y_end, x_start:x_end]
            
            if np.mean(neighborhood) > 235:  # Entorno muy blanco
                is_white_residual = True
        
        # Si es píxel residual blanco, eliminarlo
        if is_white_residual:
            result_mask[y, x] = 0
            removed_count += 1
    
    print(f"✂️  Eliminados {removed_count} píxeles blancos residuales")
    
    return result_mask

def fine_tune_existing_mask(original_image, existing_mask, tune_level=5):
    """
    Ajusta finamente una máscara existente que ya es buena
    """
    # 1. Análisis inicial de bordes
    tuned_mask = analyze_border_pixels(original_image, existing_mask, tune_level + 3)
    
    # 2. Aplicar erosión muy ligera y específica solo en bordes problemáticos
    # Crear kernel muy pequeño para erosión mínima
    kernel_tiny = np.ones((2, 2), np.uint8)
    
    # Solo aplicar en áreas que todavía podrían tener residuos
    gray = cv2.cvtColor(np.array(original_image), cv2.COLOR_RGB2GRAY)
    very_bright = gray > 245
    
    # Intersección de máscara actual y áreas muy brillantes
    problem_areas = cv2.bitwise_and(tuned_mask, very_bright.astype(np.uint8) * 255)
    
    if np.sum(problem_areas) > 0:
        # Erosionar solo las áreas problemáticas
        problem_eroded = cv2.erode(problem_areas, kernel_tiny, iterations=1)
        
        # Restar las áreas problemáticas erosionadas de la máscara
        tuned_mask = cv2.subtract(tuned_mask, cv2.subtract(problem_areas, problem_eroded))
    
    # 3. Limpieza muy suave para mantener transiciones naturales
    kernel_smooth = np.ones((2, 2), np.uint8)
    tuned_mask = cv2.morphologyEx(tuned_mask, cv2.MORPH_CLOSE, kernel_smooth)
    
    return tuned_mask

def refine_existing_result(input_path, output_path, tune_pixels=5):
    """
    Refina un resultado que ya está bien, eliminando píxeles residuales específicos
    """
    try:
        print("🎯 Ajuste FINO de resultado existente...")
        print(f"🔧 Nivel de ajuste: {tune_pixels} píxeles")
        
        # Cargar imagen original
        with Image.open(input_path) as img:
            original = img.convert('RGBA')
            original_rgb = img.convert('RGB')
            print(f"📐 Procesando imagen: {original.size}")
        
        # En lugar de generar nueva máscara, usar directamente rembg como base
        from rembg import remove, new_session
        
        print("🤖 Generando máscara base de referencia...")
        session = new_session('u2net_human_seg')
        ai_result = remove(original_rgb, session=session)
        base_mask = np.array(ai_result)[:,:,3]
        
        # Aplicar threshold conservador para tener una buena base
        _, base_mask = cv2.threshold(base_mask, 120, 255, cv2.THRESH_BINARY)
        
        print("🔧 Aplicando ajuste fino a la máscara...")
        refined_mask = fine_tune_existing_mask(original_rgb, base_mask, tune_pixels)
        
        # Aplicar una pasada adicional de análisis específico
        print("🎯 Análisis específico de píxeles residuales...")
        final_mask = analyze_border_pixels(original_rgb, refined_mask, tune_pixels + 2)
        
        # Suavizado mínimo final
        final_mask = cv2.GaussianBlur(final_mask, (2, 2), 0.5)
        _, final_mask = cv2.threshold(final_mask, 127, 255, cv2.THRESH_BINARY)
        
        # Aplicar a imagen original
        original_array = np.array(original)
        original_array[:,:,3] = final_mask
        
        result_image = Image.fromarray(original_array, 'RGBA')
        result_image.save(output_path, 'PNG')
        
        # Estadísticas comparativas
        pixels_final = np.sum(final_mask > 127)
        pixels_total = final_mask.shape[0] * final_mask.shape[1]
        porcentaje = (pixels_final / pixels_total) * 100
        
        print(f"✅ ¡Ajuste fino completado!")
        print(f"💾 Guardado en: {output_path}")
        print(f"📊 Modelo ajustado: {porcentaje:.1f}% de la imagen")
        print(f"🎯 Refinamiento aplicado con nivel {tune_pixels}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el ajuste: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("🎯 Uso: python fine_tune_borders.py <imagen_entrada> <imagen_salida> [nivel_ajuste]")
        print("📝 Niveles de ajuste fino:")
        print("   3  - Ajuste muy suave")
        print("   5  - Ajuste estándar (recomendado)")
        print("   7  - Ajuste más agresivo")
        print("   10 - Ajuste máximo")
        print("💡 Ejemplo: python fine_tune_borders.py modelo.jpg modelo_ajustado.png 5")
        print("🔧 Diseñado para refinar resultados que ya están bien")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    tune_level = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    if not os.path.exists(input_path):
        print(f"❌ Error: No se encuentra el archivo {input_path}")
        sys.exit(1)
    
    success = refine_existing_result(input_path, output_path, tune_level)
    
    if success:
        print("\n🎉 ¡Ajuste fino completado!")
        print("✅ Resultado refinado manteniendo calidad base")
        print("💡 Compara con el resultado anterior para ver la diferencia")
    else:
        print("\n💥 El ajuste falló")
        sys.exit(1)

if __name__ == "__main__":
    main()
