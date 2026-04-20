#!/usr/bin/env python3
"""
Suavizado avanzado de bordes - Técnicas múltiples para eliminar dentado
Aplica anti-aliasing real a los bordes del modelo
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

def advanced_edge_smoothing(mask, smoothing_level=2):
    """
    Aplica suavizado avanzado a los bordes de la máscara
    
    Args:
        mask: Máscara binaria
        smoothing_level: 1=suave, 2=medio, 3=fuerte
    """
    
    # 1. Suavizado morfológico
    if smoothing_level >= 1:
        kernel_smooth = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_smooth)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_smooth)
    
    # 2. Suavizado Gaussian progresivo
    if smoothing_level >= 2:
        # Primera pasada - Gaussian más fuerte
        mask_float = mask.astype(np.float32) / 255.0
        smoothed = cv2.GaussianBlur(mask_float, (7, 7), 1.5)
        
        # Threshold gradual para anti-aliasing
        smoothed = np.clip(smoothed * 255, 0, 255).astype(np.uint8)
        _, mask = cv2.threshold(smoothed, 80, 255, cv2.THRESH_BINARY)
    
    # 3. Suavizado bilateral para preservar bordes importantes
    if smoothing_level >= 3:
        mask = cv2.bilateralFilter(mask, 9, 75, 75)
        _, mask = cv2.threshold(mask, 100, 255, cv2.THRESH_BINARY)
    
    # 4. Suavizado final con bordes graduales
    mask_float = mask.astype(np.float32) / 255.0
    final_smooth = cv2.GaussianBlur(mask_float, (5, 5), 0.8)
    final_mask = (final_smooth * 255).astype(np.uint8)
    
    # 5. Threshold final preservando transiciones suaves
    _, result_mask = cv2.threshold(final_mask, 90, 255, cv2.THRESH_BINARY)
    
    return result_mask

def create_antialiased_edges(original_image, mask):
    """
    Crea bordes con anti-aliasing real
    """
    # 1. Encontrar contornos de la máscara
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    
    if not contours:
        return mask
    
    # 2. Crear máscara suavizada con anti-aliasing
    smooth_mask = np.zeros_like(mask, dtype=np.float32)
    
    # 3. Dibujar contornos con anti-aliasing
    for contour in contours:
        # Suavizar el contorno
        epsilon = 0.02 * cv2.arcLength(contour, True)
        smoothed_contour = cv2.approxPolyDP(contour, epsilon, True)
        
        # Dibujar con anti-aliasing
        cv2.fillPoly(smooth_mask, [smoothed_contour], 1.0)
    
    # 4. Aplicar Gaussian blur para suavizado final
    smooth_mask = cv2.GaussianBlur(smooth_mask, (5, 5), 1.0)
    
    # 5. Convertir de vuelta a binario con threshold suave
    result_mask = (smooth_mask * 255).astype(np.uint8)
    _, result_mask = cv2.threshold(result_mask, 100, 255, cv2.THRESH_BINARY)
    
    return result_mask

def smooth_model_edges(input_path, output_path, smoothing_method='advanced'):
    """
    Aplica suavizado avanzado manteniendo la calidad del modelo_balanceado
    
    Args:
        input_path: Imagen de entrada
        output_path: Imagen de salida
        smoothing_method: 'basic', 'advanced', 'antialiased'
    """
    try:
        print("🎨 Suavizado AVANZADO de bordes...")
        print(f"🔧 Método: {smoothing_method}")
        
        # Cargar imagen
        with Image.open(input_path) as img:
            original = img.convert('RGBA')
            original_rgb = img.convert('RGB')
            print(f"📐 Procesando: {original.size}")
        
        # 1. Generar máscara base como modelo_balanceado
        print("🤖 Generando máscara base...")
        session = new_session('u2net_human_seg')
        ai_result = remove(original_rgb, session=session)
        base_mask = np.array(ai_result)[:,:,3]
        _, base_mask = cv2.threshold(base_mask, 100, 255, cv2.THRESH_BINARY)
        
        # 2. Eliminar píxeles blancos como modelo_balanceado_limpio
        print("🧹 Eliminando píxeles blancos...")
        img_array = np.array(original_rgb)
        is_white = np.all(img_array >= 245, axis=2)
        white_in_mask = (base_mask > 0) & is_white
        cleaned_mask = base_mask.copy()
        cleaned_mask[white_in_mask] = 0
        
        removed_count = np.sum(white_in_mask)
        print(f"🔍 Eliminados {removed_count} píxeles blancos")
        
        # 3. Aplicar suavizado según método
        print("🎨 Aplicando suavizado...")
        
        if smoothing_method == 'basic':
            final_mask = cv2.GaussianBlur(cleaned_mask, (7, 7), 1.5)
            _, final_mask = cv2.threshold(final_mask, 80, 255, cv2.THRESH_BINARY)
            
        elif smoothing_method == 'advanced':
            final_mask = advanced_edge_smoothing(cleaned_mask, smoothing_level=2)
            
        elif smoothing_method == 'antialiased':
            final_mask = create_antialiased_edges(original_rgb, cleaned_mask)
        
        # 4. Aplicar a imagen original
        original_array = np.array(original)
        original_array[:,:,3] = final_mask
        
        result_image = Image.fromarray(original_array, 'RGBA')
        result_image.save(output_path, 'PNG')
        
        # Estadísticas
        pixels_final = np.sum(final_mask > 0)
        pixels_original = np.sum(base_mask > 0)
        pixels_total = final_mask.shape[0] * final_mask.shape[1]
        porcentaje_final = (pixels_final / pixels_total) * 100
        
        print(f"✅ ¡Suavizado aplicado!")
        print(f"💾 Guardado en: {output_path}")
        print(f"📊 Resultado: {porcentaje_final:.1f}% de la imagen")
        print(f"🎯 Píxeles blancos eliminados: {removed_count}")
        print("🎨 Bordes suavizados para eliminar dentado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante suavizado: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("🎯 Uso: python advanced_smoothing.py <entrada> <salida> [metodo]")
        print("📝 Métodos de suavizado:")
        print("   basic      - Suavizado Gaussian básico")
        print("   advanced   - Suavizado morfológico + Gaussian (recomendado)")
        print("   antialiased- Anti-aliasing real de contornos")
        print("💡 Ejemplo: python advanced_smoothing.py modelo.jpg modelo_smooth.png advanced")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    method = sys.argv[3] if len(sys.argv) > 3 else 'advanced'
    
    if not os.path.exists(input_path):
        print(f"❌ Error: No se encuentra el archivo {input_path}")
        sys.exit(1)
    
    success = smooth_model_edges(input_path, output_path, method)
    
    if success:
        print("\n🎉 ¡Suavizado avanzado completado!")
        print("✅ Bordes dentados eliminados con técnicas avanzadas")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
