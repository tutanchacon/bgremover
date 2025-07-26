#!/usr/bin/env python3
"""
Eliminación de últimos 5 píxeles de borde blanco
Basado en la solución balanceada pero con refinamiento final para bordes residuales
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

def detect_residual_white_border(original_image, mask, border_pixels=5):
    """
    Detecta y elimina los últimos píxeles de borde blanco residual
    
    Args:
        original_image: Imagen original RGB
        mask: Máscara ya procesada
        border_pixels: Número de píxeles de borde a analizar (5-8)
    """
    img_array = np.array(original_image)
    
    # 1. Encontrar el contorno exterior de la máscara actual
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return mask
    
    # Tomar el contorno más grande
    largest_contour = max(contours, key=cv2.contourArea)
    
    # 2. Crear una banda de análisis alrededor del borde
    # Erosionar la máscara para crear la banda interior
    kernel_inner = np.ones((border_pixels*2, border_pixels*2), np.uint8)
    inner_mask = cv2.erode(mask, kernel_inner, iterations=1)
    
    # La banda de análisis es la diferencia entre máscara original y erosionada
    border_band = cv2.subtract(mask, inner_mask)
    
    # 3. Analizar píxeles en la banda de borde
    # Convertir a diferentes espacios de color para mejor detección
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
    lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
    
    # 4. Detectar píxeles residuales blancos/claros en la banda
    # Ser más específico que antes pero no agresivo
    
    # En RGB: píxeles muy claros
    rgb_white = np.all(img_array > 235, axis=2)  # Ligeramente menos estricto que 245
    
    # En HSV: baja saturación (blancos/grises)
    low_saturation = hsv[:,:,1] < 20  # Muy baja saturación
    high_value = hsv[:,:,2] > 240     # Alto brillo
    hsv_white = low_saturation & high_value
    
    # En LAB: alto valor L (luminancia)
    lab_bright = lab[:,:,0] > 240
    
    # 5. Combinar detecciones (píxeles que son blancos en múltiples espacios)
    residual_white = (rgb_white | hsv_white) & lab_bright
    
    # 6. Solo considerar píxeles residuales que están en la banda de borde
    residual_in_border = residual_white & (border_band > 0)
    
    # 7. Crear máscara refinada eliminando píxeles residuales
    refined_mask = mask.copy()
    refined_mask[residual_in_border] = 0
    
    # 8. Suavizar muy ligeramente los nuevos bordes
    kernel_smooth = np.ones((2, 2), np.uint8)
    refined_mask = cv2.morphologyEx(refined_mask, cv2.MORPH_CLOSE, kernel_smooth)
    
    return refined_mask

def smart_white_border_removal_v2(original_image, ai_mask, border_size=25):
    """Versión mejorada de eliminación de borde blanco"""
    img_array = np.array(original_image)
    
    # 1. Máscara base conservadora
    base_mask = ai_mask.copy()
    _, base_mask = cv2.threshold(base_mask, 100, 255, cv2.THRESH_BINARY)
    
    # 2. Detectar áreas con textura (para proteger)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    texture_mask = np.abs(laplacian) > 3  # Más sensible a texturas
    
    # 3. Detectar píxeles claramente blancos
    very_white_pixels = np.all(img_array > 240, axis=2)  # Menos estricto
    
    # 4. Proteger áreas con textura
    kernel_protect = np.ones((12, 12), np.uint8)
    protected_areas = cv2.dilate(texture_mask.astype(np.uint8) * 255, kernel_protect, iterations=1)
    
    # 5. Encontrar región de borde
    kernel_edge = np.ones((4, 4), np.uint8)
    mask_eroded = cv2.erode(base_mask, kernel_edge, iterations=border_size//4)
    border_region = base_mask - mask_eroded
    
    # 6. Eliminar píxeles blancos en borde no protegido
    pixels_to_remove = (very_white_pixels & 
                       (border_region > 0) & 
                       (protected_areas == 0))
    
    refined_mask = base_mask.copy()
    refined_mask[pixels_to_remove] = 0
    
    # 7. Cerrar pequeños huecos
    kernel_close = np.ones((3, 3), np.uint8)
    refined_mask = cv2.morphologyEx(refined_mask, cv2.MORPH_CLOSE, kernel_close)
    
    return refined_mask

def final_border_cleanup(input_path, output_path, residual_pixels=5):
    """
    Limpieza final de bordes blancos residuales
    
    Args:
        input_path: Ruta de imagen de entrada
        output_path: Ruta de imagen de salida
        residual_pixels: Píxeles de borde residual a eliminar (3-8)
    """
    try:
        print("🎯 Eliminación FINAL de bordes blancos residuales...")
        print(f"🔍 Enfocado en eliminar ~{residual_pixels}px de borde restante")
        
        # Cargar imagen original
        with Image.open(input_path) as img:
            original = img.convert('RGBA')
            original_rgb = img.convert('RGB')
            print(f"📐 Procesando imagen: {original.size}")
        
        # 1. Obtener máscara base con AI
        print("🤖 Creando máscara base optimizada...")
        session = new_session('u2net_human_seg')
        ai_result = remove(original_rgb, session=session)
        ai_mask = np.array(ai_result)[:,:,3]
        
        # 2. Aplicar eliminación inteligente mejorada
        print("🧠 Eliminación inteligente de borde blanco...")
        refined_mask = smart_white_border_removal_v2(original_rgb, ai_mask, 25)
        
        # 3. Detectar y eliminar píxeles residuales específicos
        print(f"🎯 Eliminando últimos {residual_pixels}px de borde residual...")
        final_mask = detect_residual_white_border(original_rgb, refined_mask, residual_pixels)
        
        # 4. Preservar detalles importantes
        print("🛡️  Preservando detalles del modelo...")
        gray = cv2.cvtColor(np.array(original_rgb), cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 8, 25)  # Más sensible a detalles
        
        kernel_detail = np.ones((5, 5), np.uint8)
        detail_protection = cv2.dilate(edges, kernel_detail, iterations=1)
        
        # Asegurar que los detalles estén incluidos
        final_mask = cv2.bitwise_or(final_mask, detail_protection)
        
        # 5. Limpieza final muy suave
        print("✨ Refinamiento final suave...")
        
        # Solo cerrar huecos muy pequeños
        kernel_gentle = np.ones((3, 3), np.uint8)
        final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel_gentle)
        
        # Suavizado mínimo para bordes naturales
        final_mask = cv2.GaussianBlur(final_mask, (3, 3), 0.3)
        _, final_mask = cv2.threshold(final_mask, 120, 255, cv2.THRESH_BINARY)
        
        # 6. Aplicar máscara a imagen original
        original_array = np.array(original)
        original_array[:,:,3] = final_mask
        
        # 7. Crear imagen final
        result_image = Image.fromarray(original_array, 'RGBA')
        result_image.save(output_path, 'PNG')
        
        print(f"✅ ¡Bordes residuales eliminados exitosamente!")
        print(f"💾 Guardado en: {output_path}")
        
        # Estadísticas
        pixels_modelo = np.sum(final_mask > 127)
        pixels_total = final_mask.shape[0] * final_mask.shape[1]
        porcentaje = (pixels_modelo / pixels_total) * 100
        print(f"📊 Modelo final: {porcentaje:.1f}% de la imagen")
        print("🎯 Bordes blancos residuales eliminados manteniendo modelo completo")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("🎯 Uso: python final_border_cleanup.py <imagen_entrada> <imagen_salida> [pixeles_residuales]")
        print("📝 Píxeles residuales a eliminar:")
        print("   3  - Eliminación muy suave de bordes residuales")
        print("   5  - Eliminación estándar (recomendado)")
        print("   7  - Eliminación más agresiva de residuos")
        print("   8  - Eliminación máxima de bordes residuales")
        print("💡 Ejemplo: python final_border_cleanup.py modelo.jpg modelo_final.png 5")
        print("🎯 Elimina los últimos 5px de borde blanco manteniendo modelo completo")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    residual_pixels = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    if not os.path.exists(input_path):
        print(f"❌ Error: No se encuentra el archivo {input_path}")
        sys.exit(1)
    
    success = final_border_cleanup(input_path, output_path, residual_pixels)
    
    if success:
        print("\n🎉 ¡Limpieza final completada!")
        print("✅ Modelo preservado con bordes blancos residuales eliminados")
        print("💡 Si aún quedan píxeles blancos, prueba con un valor más alto (6-8)")
        print("💡 Si se perdió algo del modelo, prueba con un valor más bajo (3-4)")
    else:
        print("\n💥 La limpieza falló")
        sys.exit(1)

if __name__ == "__main__":
    main()
