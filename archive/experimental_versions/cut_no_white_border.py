#!/usr/bin/env python3
"""
Corte de modelo humano SIN borde blanco
Elimina específicamente el halo/borde blanco que queda alrededor del modelo
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

def remove_white_border_halo(image, mask, border_threshold=240, erosion_pixels=5):
    """
    Elimina el borde/halo blanco alrededor del modelo
    
    Args:
        image: Imagen original
        mask: Máscara del modelo
        border_threshold: Umbral para detectar píxeles blancos (240 = casi blanco)
        erosion_pixels: Cuántos píxeles erosionar del borde
    """
    img_array = np.array(image)
    
    # 1. Detectar píxeles blancos/claros en la imagen original
    if len(img_array.shape) == 3:
        # Convertir a escala de grises para detectar blancos
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # 2. Crear máscara de píxeles NO blancos (donde está realmente el modelo)
    non_white_mask = gray < border_threshold
    
    # 3. Combinar con la máscara original usando AND lógico
    # Solo mantener píxeles que estén en la máscara Y no sean blancos
    refined_mask = np.logical_and(mask > 127, non_white_mask)
    
    # 4. Erosionar ligeramente para eliminar el borde residual
    kernel = np.ones((erosion_pixels, erosion_pixels), np.uint8)
    refined_mask = cv2.erode(refined_mask.astype(np.uint8) * 255, kernel, iterations=1)
    
    # 5. Aplicar operación morfológica para limpiar
    kernel_clean = np.ones((3, 3), np.uint8)
    refined_mask = cv2.morphologyEx(refined_mask, cv2.MORPH_CLOSE, kernel_clean)
    
    # 6. Suavizar bordes muy levemente (solo 1 pixel)
    refined_mask = cv2.GaussianBlur(refined_mask, (3, 3), 0.5)
    
    return refined_mask

def detect_model_without_white_border(image):
    """Detecta el modelo excluyendo específicamente bordes blancos"""
    img_array = np.array(image)
    
    # 1. Convertir a HSV para mejor detección de blancos
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
    
    # 2. Definir rangos para detectar píxeles NO blancos
    # Excluir píxeles con saturación muy baja (grises/blancos)
    lower_non_white = np.array([0, 30, 30])      # Mínima saturación y valor
    upper_non_white = np.array([180, 255, 255])  # Máxima saturación y valor
    
    # 3. Crear máscara de píxeles con color (no blancos/grises)
    colored_mask = cv2.inRange(hsv, lower_non_white, upper_non_white)
    
    # 4. También detectar por contraste en escala de grises
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # 5. Detectar bordes del modelo real
    edges = cv2.Canny(gray, 20, 60)
    
    # 6. Dilatar bordes para conectar partes del modelo
    kernel = np.ones((5, 5), np.uint8)
    edges_dilated = cv2.dilate(edges, kernel, iterations=1)
    
    # 7. Combinar detección por color y bordes
    combined = cv2.bitwise_or(colored_mask, edges_dilated)
    
    # 8. Encontrar contornos del modelo real
    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # Tomar el contorno más grande (el modelo)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Crear máscara del modelo sin bordes blancos
        model_mask = np.zeros(gray.shape, np.uint8)
        cv2.fillPoly(model_mask, [largest_contour], 255)
        
        return model_mask
    
    return None

def cut_model_no_white_border(input_path, output_path, border_removal='aggressive'):
    """
    Corta el modelo eliminando completamente el borde blanco
    
    Args:
        input_path: Ruta de imagen de entrada
        output_path: Ruta de imagen de salida
        border_removal: 'light', 'medium', 'aggressive', 'extreme'
    """
    try:
        print("🎯 Cortando modelo SIN borde blanco...")
        
        # Cargar imagen original
        with Image.open(input_path) as img:
            original = img.convert('RGBA')
            original_rgb = img.convert('RGB')
            print(f"📐 Procesando imagen: {original.size}")
        
        # 1. Obtener máscara inicial con AI
        print("🤖 Detectando modelo con AI...")
        session = new_session('u2net_human_seg')
        ai_result = remove(original_rgb, session=session)
        ai_mask = np.array(ai_result)[:,:,3]
        
        # 2. Detectar modelo sin bordes blancos
        print("🎨 Detectando modelo real (sin blancos)...")
        model_mask = detect_model_without_white_border(original_rgb)
        
        # 3. Configurar niveles de eliminación de borde
        border_settings = {
            'light': {'threshold': 250, 'erosion': 2},
            'medium': {'threshold': 240, 'erosion': 4},
            'aggressive': {'threshold': 220, 'erosion': 6},
            'extreme': {'threshold': 200, 'erosion': 8}
        }
        
        settings = border_settings.get(border_removal, border_settings['aggressive'])
        
        # 4. Eliminar borde blanco
        print(f"✂️  Eliminando borde blanco (nivel: {border_removal})...")
        final_mask = remove_white_border_halo(
            original_rgb, 
            ai_mask, 
            border_threshold=settings['threshold'],
            erosion_pixels=settings['erosion']
        )
        
        # 5. Si tenemos detección adicional, combinarla
        if model_mask is not None:
            # Usar intersección para eliminar bordes blancos
            model_mask_resized = cv2.resize(model_mask, (final_mask.shape[1], final_mask.shape[0]))
            final_mask = cv2.bitwise_and(final_mask, model_mask_resized)
        
        # 6. Limpiar máscara final
        print("🧹 Limpiando bordes...")
        
        # Eliminar pequeños artefactos
        kernel_clean = np.ones((3, 3), np.uint8)
        final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_OPEN, kernel_clean)
        
        # Cerrar pequeños huecos DENTRO del modelo
        kernel_close = np.ones((7, 7), np.uint8)
        final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel_close)
        
        # 7. Aplicar threshold para bordes limpios
        _, final_mask = cv2.threshold(final_mask, 127, 255, cv2.THRESH_BINARY)
        
        # 8. Aplicar máscara a imagen original
        original_array = np.array(original)
        original_array[:,:,3] = final_mask
        
        # 9. Crear imagen final
        result_image = Image.fromarray(original_array, 'RGBA')
        result_image.save(output_path, 'PNG')
        
        print(f"✅ ¡Modelo cortado SIN borde blanco!")
        print(f"💾 Guardado en: {output_path}")
        print(f"🎯 Eliminación de borde: {border_removal}")
        
        # Estadísticas
        pixels_modelo = np.sum(final_mask > 127)
        pixels_total = final_mask.shape[0] * final_mask.shape[1]
        porcentaje = (pixels_modelo / pixels_total) * 100
        print(f"📊 Modelo limpio: {porcentaje:.1f}% de la imagen")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el corte: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("🎯 Uso: python cut_no_white_border.py <imagen_entrada> <imagen_salida> [eliminacion_borde]")
        print("📝 Niveles de eliminación de borde blanco:")
        print("   light      - Eliminación suave (threshold 250, erosión 2px)")
        print("   medium     - Eliminación media (threshold 240, erosión 4px)")
        print("   aggressive - Eliminación agresiva (threshold 220, erosión 6px)")
        print("   extreme    - Eliminación extrema (threshold 200, erosión 8px)")
        print("💡 Ejemplo: python cut_no_white_border.py modelo.jpg modelo_limpio.png aggressive")
        print("🎯 Elimina específicamente el borde blanco de 30px alrededor del modelo")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    border_removal = sys.argv[3] if len(sys.argv) > 3 else 'aggressive'
    
    if not os.path.exists(input_path):
        print(f"❌ Error: No se encuentra el archivo {input_path}")
        sys.exit(1)
    
    success = cut_model_no_white_border(input_path, output_path, border_removal)
    
    if success:
        print("\n🎉 ¡Modelo cortado limpiamente sin borde blanco!")
        print("💡 Si aún hay borde blanco, prueba con 'extreme'")
        print("💡 Si cortó demasiado del modelo, prueba con 'light'")
    else:
        print("\n💥 El corte falló")
        sys.exit(1)

if __name__ == "__main__":
    main()
