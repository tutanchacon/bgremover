#!/usr/bin/env python3
"""
Versión final - ISNet + limpieza de blancos + suavizado
Combina la mejor segmentación (ISNet) con las mejoras de limpieza desarrolladas
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

def final_complete_model_processing(input_path, output_path, smoothing=True):
    """
    Procesamiento final completo del modelo usando ISNet + mejoras
    """
    try:
        print("🎯 Procesamiento FINAL del modelo completo...")
        print("🎭 ISNet + limpieza de blancos + suavizado opcional")
        
        # Cargar imagen
        with Image.open(input_path) as img:
            original = img.convert('RGBA')
            original_rgb = img.convert('RGB')
            print(f"📐 Procesando: {original.size}")
        
        # 1. Segmentación con ISNet (mejor para modelos completos)
        print("🤖 Segmentación con ISNet-General-Use...")
        session = new_session('isnet-general-use')
        ai_result = remove(original_rgb, session=session)
        base_mask = np.array(ai_result)[:,:,3]
        
        # Threshold conservador para preservar detalles
        _, binary_mask = cv2.threshold(base_mask, 80, 255, cv2.THRESH_BINARY)
        
        pixels_base = np.sum(binary_mask > 0)
        total_pixels = binary_mask.shape[0] * binary_mask.shape[1]
        percentage_base = (pixels_base / total_pixels) * 100
        print(f"📊 ISNet capturó: {percentage_base:.1f}% de la imagen")
        
        # 2. Conectar componentes del modelo si están separados
        print("🔗 Conectando componentes del modelo...")
        num_labels, labels = cv2.connectedComponents(binary_mask)
        
        if num_labels > 2:  # Múltiples componentes
            print(f"   🔍 Conectando {num_labels-1} componentes separados")
            
            # Dilatar para conectar partes cercanas del modelo
            kernel_connect = np.ones((15, 15), np.uint8)
            connected_mask = cv2.dilate(binary_mask, kernel_connect, iterations=1)
            
            # Cerrar gaps entre partes del modelo
            kernel_close = np.ones((25, 25), np.uint8)
            connected_mask = cv2.morphologyEx(connected_mask, cv2.MORPH_CLOSE, kernel_close)
            
            # Erosionar de vuelta (menos que la dilatación)
            kernel_erode = np.ones((10, 10), np.uint8)
            connected_mask = cv2.erode(connected_mask, kernel_erode, iterations=1)
        else:
            connected_mask = binary_mask
            print("   ✅ Modelo ya está conectado")
        
        pixels_connected = np.sum(connected_mask > 0)
        percentage_connected = (pixels_connected / total_pixels) * 100
        print(f"📊 Después de conectar: {percentage_connected:.1f}%")
        
        # 3. Eliminar píxeles blancos específicos
        print("🧹 Eliminando píxeles blancos del borde...")
        img_array = np.array(original_rgb)
        is_white = np.all(img_array >= 245, axis=2)
        white_in_mask = (connected_mask > 0) & is_white
        clean_mask = connected_mask.copy()
        clean_mask[white_in_mask] = 0
        
        removed_whites = np.sum(white_in_mask)
        print(f"🔍 Eliminados {removed_whites} píxeles blancos")
        
        # 4. Aplicar suavizado si se solicita
        if smoothing:
            print("🎨 Aplicando suavizado de bordes...")
            
            # Suavizado Gaussian para eliminar dentado
            smooth_mask = cv2.GaussianBlur(clean_mask, (5, 5), 1.0)
            _, smooth_mask = cv2.threshold(smooth_mask, 100, 255, cv2.THRESH_BINARY)
            
            # Segunda pasada más suave
            final_mask = cv2.GaussianBlur(smooth_mask, (3, 3), 0.3)
            _, final_mask = cv2.threshold(final_mask, 120, 255, cv2.THRESH_BINARY)
        else:
            final_mask = clean_mask
            print("⏭️ Saltando suavizado")
        
        # 5. Limpieza final mínima
        print("✨ Limpieza final...")
        kernel_clean = np.ones((3, 3), np.uint8)
        final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel_clean)
        
        # 6. Aplicar a imagen original
        original_array = np.array(original)
        original_array[:,:,3] = final_mask
        
        result_image = Image.fromarray(original_array, 'RGBA')
        result_image.save(output_path, 'PNG')
        
        # Estadísticas finales
        pixels_final = np.sum(final_mask > 0)
        percentage_final = (pixels_final / total_pixels) * 100
        
        print(f"✅ ¡Procesamiento final completado!")
        print(f"💾 Guardado en: {output_path}")
        print(f"📊 Resultado final: {percentage_final:.1f}% de la imagen")
        print(f"🎯 Mejora total: {percentage_final - percentage_base:.1f}% vs ISNet base")
        print("🎭 Modelo completo con bordes limpios")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante procesamiento final: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("🎯 Uso: python final_model_processing.py <entrada> <salida> [suavizado]")
        print("📝 Opciones de suavizado:")
        print("   true  - Aplicar suavizado de bordes (recomendado)")
        print("   false - Sin suavizado (solo limpieza)")
        print("💡 Ejemplo: python final_model_processing.py personaje.jpg resultado_final.png true")
        print("🎭 Versión definitiva: ISNet + limpieza + suavizado")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    apply_smoothing = sys.argv[3].lower() != 'false' if len(sys.argv) > 3 else True
    
    if not os.path.exists(input_path):
        print(f"❌ Error: No se encuentra el archivo {input_path}")
        sys.exit(1)
    
    success = final_complete_model_processing(input_path, output_path, apply_smoothing)
    
    if success:
        print("\n🎉 ¡Procesamiento final exitoso!")
        print("✅ Modelo completo capturado y procesado")
        print("🎭 Versión definitiva lista")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
