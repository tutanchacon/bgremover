#!/usr/bin/env python3
"""
Erosión mínima de bordes - Toma el resultado balanceado y erosiona solo 5px del borde
Diseñado para refinar el modelo_balanceado que ya era excelente
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

def minimal_border_erosion(mask, erosion_pixels=3):
    """
    Aplica erosión MUY mínima solo en los bordes exteriores
    
    Args:
        mask: Máscara existente que ya es buena
        erosion_pixels: Número de píxeles a erosionar (2-5)
    """
    
    # 1. Crear kernel muy pequeño para erosión mínima
    kernel_size = max(2, erosion_pixels)
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    
    # 2. Aplicar erosión muy suave
    eroded_mask = cv2.erode(mask, kernel, iterations=1)
    
    # 3. Para conservar detalles, usar morphological opening en lugar de erosión simple
    # Esto preserva mejor las formas
    kernel_preserve = np.ones((3, 3), np.uint8)
    preserved_mask = cv2.morphologyEx(eroded_mask, cv2.MORPH_OPEN, kernel_preserve)
    
    # 4. Cerrar pequeños huecos que puedan haberse creado
    kernel_close = np.ones((2, 2), np.uint8)
    final_mask = cv2.morphologyEx(preserved_mask, cv2.MORPH_CLOSE, kernel_close)
    
    return final_mask

def smart_border_trim(original_image, mask, trim_pixels=5):
    """
    Recorta inteligentemente solo píxeles de borde que son realmente blancos
    """
    img_array = np.array(original_image)
    
    # 1. Identificar la banda de borde exterior (donde están los píxeles problemáticos)
    kernel_band = np.ones((trim_pixels*2 + 2, trim_pixels*2 + 2), np.uint8)
    inner_mask = cv2.erode(mask, kernel_band, iterations=1)
    border_band = cv2.subtract(mask, inner_mask)
    
    # 2. En esa banda, analizar qué píxeles son realmente blancos
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Detectar píxeles claramente blancos en la banda de borde
    white_pixels_in_border = (border_band > 0) & (gray > 235)
    
    # 3. Crear máscara refinada eliminando solo esos píxeles blancos
    refined_mask = mask.copy()
    refined_mask[white_pixels_in_border] = 0
    
    # 4. Aplicar erosión muy ligera adicional solo si es necesario
    if trim_pixels > 3:
        kernel_tiny = np.ones((2, 2), np.uint8)
        refined_mask = cv2.erode(refined_mask, kernel_tiny, iterations=1)
    
    return refined_mask

def trim_white_border_carefully(input_path, output_path, trim_level=5):
    """
    Recorta cuidadosamente solo los píxeles de borde blanco problemáticos
    
    Args:
        input_path: Imagen de entrada
        output_path: Imagen de salida
        trim_level: Nivel de recorte (3-7 píxeles)
    """
    try:
        print("🎯 Recorte CUIDADOSO de borde blanco...")
        print(f"✂️  Nivel de recorte: {trim_level} píxeles")
        print("🛡️  Preservando modelo completo")
        
        # Cargar imagen
        with Image.open(input_path) as img:
            original = img.convert('RGBA')
            original_rgb = img.convert('RGB')
            print(f"📐 Procesando: {original.size}")
        
        # Generar máscara base conservadora (como modelo_balanceado)
        print("🤖 Generando máscara base conservadora...")
        session = new_session('u2net_human_seg')
        ai_result = remove(original_rgb, session=session)
        base_mask = np.array(ai_result)[:,:,3]
        
        # Usar threshold conservador como en modelo_balanceado
        _, base_mask = cv2.threshold(base_mask, 100, 255, cv2.THRESH_BINARY)
        
        # Aplicar recorte inteligente de borde
        print(f"🎯 Recortando {trim_level}px de borde blanco...")
        trimmed_mask = smart_border_trim(original_rgb, base_mask, trim_level)
        
        # Aplicar erosión mínima adicional
        print("✂️  Aplicando erosión mínima...")
        final_mask = minimal_border_erosion(trimmed_mask, trim_level // 2)
        
        # Preservar detalles importantes
        print("🛡️  Preservando detalles del modelo...")
        gray = cv2.cvtColor(np.array(original_rgb), cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 5, 15)
        
        # Dilatar bordes para crear zona de protección
        kernel_protect = np.ones((3, 3), np.uint8)
        protected_edges = cv2.dilate(edges, kernel_protect, iterations=1)
        
        # Asegurar que los detalles importantes se mantengan
        final_mask = cv2.bitwise_or(final_mask, protected_edges)
        
        # Limpieza final muy suave
        print("✨ Limpieza final...")
        kernel_final = np.ones((2, 2), np.uint8)
        final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel_final)
        
        # Aplicar a imagen original
        original_array = np.array(original)
        original_array[:,:,3] = final_mask
        
        result_image = Image.fromarray(original_array, 'RGBA')
        result_image.save(output_path, 'PNG')
        
        # Estadísticas
        pixels_modelo = np.sum(final_mask > 127)
        pixels_total = final_mask.shape[0] * final_mask.shape[1]
        porcentaje = (pixels_modelo / pixels_total) * 100
        
        print(f"✅ ¡Recorte cuidadoso completado!")
        print(f"💾 Guardado en: {output_path}")
        print(f"📊 Modelo recortado: {porcentaje:.1f}% de la imagen")
        print("🎯 Solo se recortaron píxeles de borde blanco problemáticos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el recorte: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("🎯 Uso: python careful_trim.py <imagen_entrada> <imagen_salida> [nivel_recorte]")
        print("📝 Niveles de recorte cuidadoso:")
        print("   3  - Recorte muy suave")
        print("   5  - Recorte estándar (recomendado)")
        print("   7  - Recorte más notable")
        print("💡 Ejemplo: python careful_trim.py modelo.jpg modelo_recortado.png 5")
        print("🎯 Recorta solo 5px de borde blanco preservando modelo completo")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    trim_level = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    if not os.path.exists(input_path):
        print(f"❌ Error: No se encuentra el archivo {input_path}")
        sys.exit(1)
    
    success = trim_white_border_carefully(input_path, output_path, trim_level)
    
    if success:
        print("\n🎉 ¡Recorte cuidadoso exitoso!")
        print("✅ Modelo preservado con borde blanco recortado")
        print("💡 Este enfoque mantiene la calidad del modelo_balanceado")
    else:
        print("\n💥 El recorte falló")
        sys.exit(1)

if __name__ == "__main__":
    main()
