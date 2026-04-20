#!/usr/bin/env python3
"""
Eliminación de píxeles blancos basada en modelo_balanceado
Replica exactamente modelo_balanceado y luego elimina solo píxeles blancos
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

def replicate_balanced_model_approach(original_image):
    """
    Replica exactamente el enfoque de modelo_balanceado
    """
    img_array = np.array(original_image)
    
    # 1. Usar AI especializada en humanos (igual que modelo_balanceado)
    session = new_session('u2net_human_seg')
    ai_result = remove(original_image, session=session)
    ai_mask = np.array(ai_result)[:,:,3]
    
    # 2. Threshold conservador igual que modelo_balanceado
    _, base_mask = cv2.threshold(ai_mask, 100, 255, cv2.THRESH_BINARY)
    
    # 3. Detectar texturas para proteger (igual que modelo_balanceado)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    texture_mask = np.abs(laplacian) > 3
    
    # 4. Proteger áreas con textura
    kernel_protect = np.ones((12, 12), np.uint8)
    protected_areas = cv2.dilate(texture_mask.astype(np.uint8) * 255, kernel_protect, iterations=1)
    
    # 5. Detectar píxeles blancos
    very_white_pixels = np.all(img_array > 240, axis=2)
    
    # 6. Encontrar región de borde
    kernel_edge = np.ones((4, 4), np.uint8)
    mask_eroded = cv2.erode(base_mask, kernel_edge, iterations=25//4)
    border_region = base_mask - mask_eroded
    
    # 7. Eliminar píxeles blancos solo en borde no protegido
    pixels_to_remove = (very_white_pixels & 
                       (border_region > 0) & 
                       (protected_areas == 0))
    
    refined_mask = base_mask.copy()
    refined_mask[pixels_to_remove] = 0
    
    # 8. Cerrar pequeños huecos (igual que modelo_balanceado)
    kernel_close = np.ones((3, 3), np.uint8)
    refined_mask = cv2.morphologyEx(refined_mask, cv2.MORPH_CLOSE, kernel_close)
    
    # 9. Preservar detalles importantes
    edges = cv2.Canny(gray, 8, 25)
    kernel_detail = np.ones((5, 5), np.uint8)
    detail_protection = cv2.dilate(edges, kernel_detail, iterations=1)
    refined_mask = cv2.bitwise_or(refined_mask, detail_protection)
    
    # 10. Limpieza final suave
    kernel_gentle = np.ones((3, 3), np.uint8)
    final_mask = cv2.morphologyEx(refined_mask, cv2.MORPH_CLOSE, kernel_gentle)
    final_mask = cv2.GaussianBlur(final_mask, (3, 3), 0.3)
    _, final_mask = cv2.threshold(final_mask, 120, 255, cv2.THRESH_BINARY)
    
    return final_mask

def extra_white_pixel_cleanup(original_image, mask, aggressiveness=1):
    """
    Limpieza extra de píxeles blancos después del modelo_balanceado
    """
    img_array = np.array(original_image)
    result_mask = mask.copy()
    
    # Configurar agresividad
    thresholds = {
        1: 248,  # Solo píxeles extremadamente blancos
        2: 245,  # Píxeles muy blancos
        3: 242,  # Píxeles claramente blancos
        4: 238   # Píxeles blancos obvios
    }
    
    white_threshold = thresholds.get(aggressiveness, 245)
    
    # Detectar píxeles blancos
    is_white = np.all(img_array >= white_threshold, axis=2)
    
    # Solo eliminar los que están en la máscara actual
    white_in_mask = (mask > 0) & is_white
    
    # Eliminar esos píxeles
    result_mask[white_in_mask] = 0
    
    removed_count = np.sum(white_in_mask)
    print(f"🧹 Eliminados {removed_count} píxeles blancos adicionales (umbral {white_threshold})")
    
    return result_mask

def balanced_model_with_white_cleanup(input_path, output_path, cleanup_level=2):
    """
    Replica modelo_balanceado y luego elimina píxeles blancos específicos
    """
    try:
        print("🎯 Replicando modelo_balanceado + limpieza de blancos...")
        print(f"🧹 Nivel de limpieza: {cleanup_level}")
        
        # Cargar imagen
        with Image.open(input_path) as img:
            original = img.convert('RGBA')
            original_rgb = img.convert('RGB')
            print(f"📐 Procesando: {original.size}")
        
        # 1. Aplicar enfoque exacto de modelo_balanceado
        print("🤖 Aplicando enfoque de modelo_balanceado...")
        balanced_mask = replicate_balanced_model_approach(original_rgb)
        
        pixels_balanced = np.sum(balanced_mask > 0)
        pixels_total = balanced_mask.shape[0] * balanced_mask.shape[1]
        porcentaje_balanced = (pixels_balanced / pixels_total) * 100
        print(f"📊 Resultado estilo modelo_balanceado: {porcentaje_balanced:.1f}%")
        
        # 2. Aplicar limpieza extra de píxeles blancos
        print("🧹 Aplicando limpieza extra de píxeles blancos...")
        cleaned_mask = extra_white_pixel_cleanup(original_rgb, balanced_mask, cleanup_level)
        
        # 3. Aplicar suavizado más notable para bordes suaves
        print("🎨 Aplicando suavizado para eliminar dentado...")
        
        # Suavizado más fuerte para bordes visiblemente suaves
        blurred_mask = cv2.GaussianBlur(cleaned_mask, (5, 5), 1.0)
        
        # Threshold más bajo para preservar el suavizado
        _, final_mask = cv2.threshold(blurred_mask, 100, 255, cv2.THRESH_BINARY)
        
        # Aplicar una segunda pasada de suavizado muy ligero
        final_mask = cv2.GaussianBlur(final_mask, (3, 3), 0.3)
        _, final_mask = cv2.threshold(final_mask, 120, 255, cv2.THRESH_BINARY)
        
        # 4. Aplicar a imagen original
        original_array = np.array(original)
        original_array[:,:,3] = final_mask
        
        result_image = Image.fromarray(original_array, 'RGBA')
        result_image.save(output_path, 'PNG')
        
        # Estadísticas finales
        pixels_final = np.sum(final_mask > 0)
        porcentaje_final = (pixels_final / pixels_total) * 100
        
        print(f"✅ ¡Procesamiento completado!")
        print(f"💾 Guardado en: {output_path}")
        print(f"📊 Modelo_balanceado: {porcentaje_balanced:.1f}% → Final: {porcentaje_final:.1f}%")
        print(f"🎯 Píxeles blancos eliminados: {pixels_balanced - pixels_final}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("🎯 Uso: python balanced_plus_cleanup.py <entrada> <salida> [nivel_limpieza]")
        print("📝 Niveles de limpieza de blancos:")
        print("   1 - Solo píxeles extremadamente blancos (248+)")
        print("   2 - Píxeles muy blancos (245+) [recomendado]")
        print("   3 - Píxeles claramente blancos (242+)")
        print("   4 - Píxeles blancos obvios (238+)")
        print("💡 Ejemplo: python balanced_plus_cleanup.py modelo.jpg resultado.png 2")
        print("🎯 Replica modelo_balanceado + elimina píxeles blancos específicos")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    cleanup_level = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    
    if not os.path.exists(input_path):
        print(f"❌ Error: No se encuentra el archivo {input_path}")
        sys.exit(1)
    
    success = balanced_model_with_white_cleanup(input_path, output_path, cleanup_level)
    
    if success:
        print("\n🎉 ¡Éxito!")
        print("✅ Calidad de modelo_balanceado con píxeles blancos eliminados")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
