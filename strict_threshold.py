#!/usr/bin/env python3
"""
Ajuste de threshold para eliminar píxeles de borde específicos
Cambia el umbral de decisión para ser más estricto en los bordes
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

def adjust_mask_threshold_for_borders(original_image, mask, strict_threshold=150):
    """
    Ajusta el threshold de la máscara para ser más estricto en bordes
    """
    img_array = np.array(original_image)
    
    # 1. Encontrar región de borde
    kernel_border = np.ones((10, 10), np.uint8)
    eroded_mask = cv2.erode(mask, kernel_border, iterations=1)
    border_region = cv2.subtract(mask, eroded_mask)
    
    # 2. En la región de borde, ser más estricto con píxeles claros
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # 3. Crear nueva máscara con threshold más alto en bordes
    adjusted_mask = mask.copy()
    
    # En región de borde, eliminar píxeles con valor gris > 220
    border_pixels_to_remove = (border_region > 0) & (gray > 220)
    adjusted_mask[border_pixels_to_remove] = 0
    
    # 4. Aplicar threshold más estricto globalmente
    _, adjusted_mask = cv2.threshold(adjusted_mask, strict_threshold, 255, cv2.THRESH_BINARY)
    
    return adjusted_mask

def create_strict_border_mask(input_path, output_path, threshold_level=150):
    """
    Crea máscara con threshold más estricto para eliminar bordes blancos
    """
    try:
        print("🎯 Creando máscara con threshold ESTRICTO...")
        print(f"📊 Nivel de threshold: {threshold_level}")
        
        # Cargar imagen
        with Image.open(input_path) as img:
            original = img.convert('RGBA')
            original_rgb = img.convert('RGB')
            print(f"📐 Procesando imagen: {original.size}")
        
        # Generar máscara base
        print("🤖 Generando máscara base...")
        session = new_session('u2net_human_seg')
        ai_result = remove(original_rgb, session=session)
        base_mask = np.array(ai_result)[:,:,3]
        
        # Aplicar threshold estricto
        print(f"🔧 Aplicando threshold estricto ({threshold_level})...")
        strict_mask = adjust_mask_threshold_for_borders(original_rgb, base_mask, threshold_level)
        
        # Limpiar ligeramente
        kernel_clean = np.ones((2, 2), np.uint8)
        strict_mask = cv2.morphologyEx(strict_mask, cv2.MORPH_CLOSE, kernel_clean)
        
        # Aplicar a imagen
        original_array = np.array(original)
        original_array[:,:,3] = strict_mask
        
        result_image = Image.fromarray(original_array, 'RGBA')
        result_image.save(output_path, 'PNG')
        
        # Estadísticas
        pixels_modelo = np.sum(strict_mask > 127)
        pixels_total = strict_mask.shape[0] * strict_mask.shape[1]
        porcentaje = (pixels_modelo / pixels_total) * 100
        
        print(f"✅ Máscara estricta creada!")
        print(f"💾 Guardado en: {output_path}")
        print(f"📊 Modelo con threshold {threshold_level}: {porcentaje:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("🎯 Uso: python strict_threshold.py <entrada> <salida> [threshold]")
        print("📝 Niveles de threshold:")
        print("   140 - Más inclusivo")
        print("   150 - Estándar estricto") 
        print("   160 - Muy estricto")
        print("   170 - Extremadamente estricto")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    threshold = int(sys.argv[3]) if len(sys.argv) > 3 else 150
    
    success = create_strict_border_mask(input_path, output_path, threshold)
    
    if success:
        print("\n🎉 ¡Threshold estricto aplicado!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
