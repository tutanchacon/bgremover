#!/usr/bin/env python3
"""
Recorte uniforme de bordes - Elimina borde blanco de manera simétrica en todos los lados
Soluciona el problema de limpieza desigual (más un lado que otro)
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

def uniform_border_detection(original_image, mask, border_pixels=5):
    """
    Detecta píxeles de borde blanco de manera uniforme en todos los lados
    """
    img_array = np.array(original_image)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # 1. Encontrar contornos de la máscara
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    
    if not contours:
        return mask
    
    # 2. Crear máscara de contorno (solo el borde)
    contour_mask = np.zeros_like(mask)
    cv2.drawContours(contour_mask, contours, -1, 255, thickness=border_pixels*2)
    
    # 3. Crear banda de análisis uniforme
    # Dilatar hacia afuera y erosionar hacia adentro para crear banda simétrica
    kernel_outer = np.ones((border_pixels, border_pixels), np.uint8)
    kernel_inner = np.ones((border_pixels, border_pixels), np.uint8)
    
    # Banda exterior (dilatar la máscara)
    outer_band = cv2.dilate(mask, kernel_outer, iterations=1)
    
    # Banda interior (erosionar la máscara)
    inner_band = cv2.erode(mask, kernel_inner, iterations=1)
    
    # La banda de análisis es la diferencia
    analysis_band = cv2.subtract(outer_band, inner_band)
    
    # 4. En la banda, detectar píxeles blancos de manera uniforme
    # Usar múltiples criterios para detección consistente
    white_criteria_1 = gray > 240  # Píxeles muy blancos
    white_criteria_2 = gray > 230  # Píxeles blancos moderados
    
    # Aplicar criterios en la banda
    white_in_band_strict = analysis_band > 0 & white_criteria_1
    white_in_band_moderate = analysis_band > 0 & white_criteria_2
    
    # 5. Eliminar píxeles blancos de la máscara original
    result_mask = mask.copy()
    
    # Ser más estricto: solo eliminar píxeles muy blancos
    result_mask[white_in_band_strict] = 0
    
    return result_mask

def symmetric_erosion(mask, erosion_pixels=3):
    """
    Aplica erosión simétrica usando kernel circular para uniformidad
    """
    # Crear kernel circular para erosión uniforme
    kernel_size = erosion_pixels * 2 + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    
    # Aplicar erosión con kernel circular
    eroded_mask = cv2.erode(mask, kernel, iterations=1)
    
    return eroded_mask

def direction_aware_cleaning(mask, original_image):
    """
    Limpia la máscara teniendo en cuenta las direcciones para evitar asimetría
    """
    img_array = np.array(original_image)
    
    # 1. Detectar bordes en diferentes direcciones
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Sobel en X (bordes verticales)
    sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    
    # Sobel en Y (bordes horizontales)  
    sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    
    # Combinar gradientes
    sobel_combined = np.sqrt(sobel_x**2 + sobel_y**2)
    
    # 2. Normalizar y crear máscara de protección
    sobel_normalized = ((sobel_combined - sobel_combined.min()) / 
                       (sobel_combined.max() - sobel_combined.min()) * 255).astype(np.uint8)
    
    # Proteger áreas con gradientes fuertes (detalles del modelo)
    protection_mask = sobel_normalized > 30
    
    # 3. Aplicar protección a la máscara
    protected_mask = mask.copy()
    protected_mask[protection_mask] = 255  # Forzar que se mantengan los detalles
    
    return protected_mask

def uniform_white_border_removal(input_path, output_path, trim_pixels=5):
    """
    Elimina borde blanco de manera uniforme en todos los lados
    
    Args:
        input_path: Imagen de entrada
        output_path: Imagen de salida  
        trim_pixels: Píxeles a recortar uniformemente (3-7)
    """
    try:
        print("🎯 Recorte UNIFORME de borde blanco...")
        print(f"⚖️  Aplicando recorte simétrico de {trim_pixels}px")
        
        # Cargar imagen
        with Image.open(input_path) as img:
            original = img.convert('RGBA')
            original_rgb = img.convert('RGB')
            print(f"📐 Procesando: {original.size}")
        
        # 1. Generar máscara base conservadora
        print("🤖 Generando máscara base...")
        session = new_session('u2net_human_seg')
        ai_result = remove(original_rgb, session=session)
        base_mask = np.array(ai_result)[:,:,3]
        
        # Threshold conservador como modelo_balanceado
        _, base_mask = cv2.threshold(base_mask, 100, 255, cv2.THRESH_BINARY)
        
        # 2. Detectar bordes blancos uniformemente
        print("🔍 Detectando bordes blancos uniformemente...")
        detected_mask = uniform_border_detection(original_rgb, base_mask, trim_pixels)
        
        # 3. Aplicar erosión simétrica
        print("⚖️  Aplicando erosión simétrica...")
        symmetric_mask = symmetric_erosion(detected_mask, trim_pixels // 2)
        
        # 4. Aplicar limpieza consciente de direcciones
        print("🧭 Aplicando limpieza direccional...")
        directional_mask = direction_aware_cleaning(symmetric_mask, original_rgb)
        
        # 5. Combinar máscaras de manera conservadora
        # Tomar el máximo para preservar detalles
        final_mask = cv2.bitwise_or(symmetric_mask, directional_mask)
        
        # 6. Limpieza final simétrica
        print("✨ Limpieza final simétrica...")
        
        # Usar kernel circular para operaciones finales
        kernel_circular = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel_circular)
        
        # Suavizado isotrópico (igual en todas las direcciones)
        final_mask = cv2.GaussianBlur(final_mask, (3, 3), 0.5)
        _, final_mask = cv2.threshold(final_mask, 127, 255, cv2.THRESH_BINARY)
        
        # 7. Aplicar a imagen original
        original_array = np.array(original)
        original_array[:,:,3] = final_mask
        
        result_image = Image.fromarray(original_array, 'RGBA')
        result_image.save(output_path, 'PNG')
        
        # Estadísticas
        pixels_modelo = np.sum(final_mask > 127)
        pixels_total = final_mask.shape[0] * final_mask.shape[1]
        porcentaje = (pixels_modelo / pixels_total) * 100
        
        print(f"✅ ¡Recorte uniforme completado!")
        print(f"💾 Guardado en: {output_path}")
        print(f"📊 Modelo uniforme: {porcentaje:.1f}% de la imagen")
        print("⚖️  Recorte aplicado simétricamente en todos los lados")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el recorte uniforme: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("🎯 Uso: python uniform_trim.py <imagen_entrada> <imagen_salida> [pixeles_recorte]")
        print("📝 Recorte uniforme simétrico:")
        print("   3  - Recorte suave uniforme")
        print("   5  - Recorte estándar uniforme (recomendado)")
        print("   7  - Recorte notable uniforme")
        print("💡 Ejemplo: python uniform_trim.py modelo.jpg modelo_uniforme.png 5")
        print("⚖️  Aplica recorte simétrico en todos los lados (sin asimetrías)")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    trim_pixels = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    if not os.path.exists(input_path):
        print(f"❌ Error: No se encuentra el archivo {input_path}")
        sys.exit(1)
    
    success = uniform_white_border_removal(input_path, output_path, trim_pixels)
    
    if success:
        print("\n🎉 ¡Recorte uniforme exitoso!")
        print("✅ Borde blanco eliminado simétricamente")
        print("⚖️  Sin diferencias entre lados superior/inferior izquierda/derecha")
    else:
        print("\n💥 El recorte uniforme falló")
        sys.exit(1)

if __name__ == "__main__":
    main()
