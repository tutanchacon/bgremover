#!/usr/bin/env python3
"""
Segmentación con ISNet - Modelo general más efectivo para figuras completas
Usa el modelo isnet-general-use que es mejor para modelos/personajes complejos
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

def isnet_segmentation_with_cleanup(input_path, output_path):
    """
    Segmentación usando ISNet con limpieza específica
    """
    try:
        print("🎯 Segmentación con ISNet-General-Use...")
        print("🎭 Optimizado para figuras y personajes completos")
        
        # Cargar imagen
        with Image.open(input_path) as img:
            original = img.convert('RGBA')
            original_rgb = img.convert('RGB')
            print(f"📐 Procesando: {original.size}")
        
        # 1. Usar ISNet-General-Use (mejor para figuras completas)
        print("🤖 Aplicando ISNet-General-Use...")
        session = new_session('isnet-general-use')
        ai_result = remove(original_rgb, session=session)
        base_mask = np.array(ai_result)[:,:,3]
        
        # Estadísticas iniciales
        pixels_base = np.sum(base_mask > 0)
        total_pixels = base_mask.shape[0] * base_mask.shape[1]
        percentage_base = (pixels_base / total_pixels) * 100
        print(f"📊 ISNet capturó: {percentage_base:.1f}% de la imagen")
        
        # 2. Threshold conservador
        _, binary_mask = cv2.threshold(base_mask, 80, 255, cv2.THRESH_BINARY)
        
        pixels_binary = np.sum(binary_mask > 0)
        percentage_binary = (pixels_binary / total_pixels) * 100
        print(f"📊 Después de threshold 80: {percentage_binary:.1f}%")
        
        # 3. Conectar componentes separados
        print("🔗 Conectando componentes del modelo...")
        
        # Encontrar componentes
        num_labels, labels = cv2.connectedComponents(binary_mask)
        print(f"   🔍 Encontrados {num_labels-1} componentes")
        
        if num_labels > 2:  # Múltiples componentes
            # Dilatar para conectar partes cercanas
            kernel_connect = np.ones((20, 20), np.uint8)
            connected_mask = cv2.dilate(binary_mask, kernel_connect, iterations=1)
            
            # Cerrar gaps grandes
            kernel_close = np.ones((30, 30), np.uint8)
            connected_mask = cv2.morphologyEx(connected_mask, cv2.MORPH_CLOSE, kernel_close)
            
            # Erosionar de vuelta (menos que la dilatación)
            kernel_erode = np.ones((15, 15), np.uint8)
            connected_mask = cv2.erode(connected_mask, kernel_erode, iterations=1)
        else:
            connected_mask = binary_mask
        
        pixels_connected = np.sum(connected_mask > 0)
        percentage_connected = (pixels_connected / total_pixels) * 100
        print(f"📊 Después de conectar: {percentage_connected:.1f}%")
        
        # 4. Eliminar píxeles blancos
        print("🧹 Eliminando píxeles blancos...")
        img_array = np.array(original_rgb)
        is_white = np.all(img_array >= 245, axis=2)
        white_in_mask = (connected_mask > 0) & is_white
        clean_mask = connected_mask.copy()
        clean_mask[white_in_mask] = 0
        
        removed_whites = np.sum(white_in_mask)
        print(f"🔍 Eliminados {removed_whites} píxeles blancos")
        
        # 5. Limpieza final suave
        print("✨ Limpieza final...")
        
        # Cerrar huecos pequeños
        kernel_clean = np.ones((5, 5), np.uint8)
        final_mask = cv2.morphologyEx(clean_mask, cv2.MORPH_CLOSE, kernel_clean)
        
        # Suavizado muy ligero
        final_mask = cv2.GaussianBlur(final_mask, (3, 3), 0.5)
        _, final_mask = cv2.threshold(final_mask, 127, 255, cv2.THRESH_BINARY)
        
        # 6. Aplicar a imagen original
        original_array = np.array(original)
        original_array[:,:,3] = final_mask
        
        result_image = Image.fromarray(original_array, 'RGBA')
        result_image.save(output_path, 'PNG')
        
        # Estadísticas finales
        pixels_final = np.sum(final_mask > 0)
        percentage_final = (pixels_final / total_pixels) * 100
        
        print(f"✅ ¡Segmentación ISNet completada!")
        print(f"💾 Guardado en: {output_path}")
        print(f"📊 Resultado final: {percentage_final:.1f}% de la imagen")
        print(f"🎯 ISNet vs U²-Net: Debería capturar mejor el modelo completo")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante segmentación ISNet: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("🎯 Uso: python isnet_segmentation.py <imagen_entrada> <imagen_salida>")
        print("🎭 Usa ISNet-General-Use para mejor captura de modelos completos")
        print("💡 Ejemplo: python isnet_segmentation.py personaje.jpg personaje_isnet.png")
        print("🤖 ISNet es mejor que U²-Net para figuras complejas")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    if not os.path.exists(input_path):
        print(f"❌ Error: No se encuentra el archivo {input_path}")
        sys.exit(1)
    
    success = isnet_segmentation_with_cleanup(input_path, output_path)
    
    if success:
        print("\n🎉 ¡Segmentación ISNet exitosa!")
        print("✅ Debería capturar mejor el modelo completo")
        print("🎭 ISNet está optimizado para figuras complejas")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
