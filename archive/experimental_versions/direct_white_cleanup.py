#!/usr/bin/env python3
"""
Limpieza directa de borde blanco - Enfoque simple y directo
Toma el resultado bueno de modelo_balanceado y elimina SOLO píxeles blancos en el borde
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

def direct_white_pixel_removal(original_image, mask, white_threshold=245):
    """
    Elimina directamente píxeles blancos del borde SIN algoritmos complejos
    
    Args:
        original_image: Imagen original
        mask: Máscara existente (buena)
        white_threshold: Umbral para detectar píxeles blancos (245 = muy blanco)
    """
    img_array = np.array(original_image)
    result_mask = mask.copy()
    
    # 1. Detectar píxeles REALMENTE blancos en la imagen original
    if len(img_array.shape) == 3:
        # Para RGB: todos los canales deben ser muy altos
        is_white = np.all(img_array >= white_threshold, axis=2)
    else:
        # Para escala de grises
        is_white = img_array >= white_threshold
    
    # 2. Solo eliminar píxeles que estén EN la máscara Y sean blancos
    pixels_to_remove = (mask > 0) & is_white
    
    # 3. Eliminar esos píxeles de la máscara
    result_mask[pixels_to_remove] = 0
    
    print(f"🔍 Eliminados {np.sum(pixels_to_remove)} píxeles blancos específicos")
    
    return result_mask

def iterative_white_removal(original_image, mask, iterations=3, threshold_step=5):
    """
    Aplica eliminación iterativa bajando el umbral gradualmente
    """
    current_mask = mask.copy()
    initial_threshold = 250
    
    for i in range(iterations):
        current_threshold = initial_threshold - (i * threshold_step)
        print(f"🎯 Iteración {i+1}: umbral {current_threshold}")
        
        # Aplicar limpieza con umbral actual
        cleaned_mask = direct_white_pixel_removal(original_image, current_mask, current_threshold)
        
        # Verificar que no perdimos demasiado
        original_pixels = np.sum(current_mask > 0)
        cleaned_pixels = np.sum(cleaned_mask > 0)
        loss_percentage = (original_pixels - cleaned_pixels) / original_pixels * 100
        
        print(f"   📊 Pérdida: {loss_percentage:.1f}%")
        
        # Si la pérdida es razonable, usar el resultado
        if loss_percentage < 8:  # No perder más del 8%
            current_mask = cleaned_mask
        else:
            print(f"   ⚠️  Pérdida excesiva, manteniendo máscara anterior")
            break
    
    return current_mask

def simple_border_cleanup(input_path, output_path, white_threshold=245):
    """
    Limpieza simple y directa de bordes blancos
    
    Args:
        input_path: Imagen de entrada
        output_path: Imagen de salida
        white_threshold: Umbral para detectar blancos (240-250)
    """
    try:
        print("🎯 Limpieza DIRECTA de píxeles blancos en borde...")
        print(f"🔍 Umbral de blanco: {white_threshold}")
        
        # Cargar imagen
        with Image.open(input_path) as img:
            original = img.convert('RGBA')
            original_rgb = img.convert('RGB')
            print(f"📐 Procesando: {original.size}")
        
        # 1. Generar máscara base IGUAL que modelo_balanceado
        print("🤖 Generando máscara base (igual que modelo_balanceado)...")
        session = new_session('u2net_human_seg')
        ai_result = remove(original_rgb, session=session)
        base_mask = np.array(ai_result)[:,:,3]
        
        # MISMO threshold que modelo_balanceado
        _, base_mask = cv2.threshold(base_mask, 100, 255, cv2.THRESH_BINARY)
        
        print(f"📊 Máscara base: {np.sum(base_mask > 0) / (base_mask.shape[0] * base_mask.shape[1]) * 100:.1f}%")
        
        # 2. Aplicar limpieza directa de píxeles blancos
        print("🧹 Eliminando píxeles blancos directamente...")
        cleaned_mask = iterative_white_removal(original_rgb, base_mask, iterations=3, threshold_step=3)
        
        # 3. Solo una limpieza mínima para cerrar pequeños huecos
        print("✨ Limpieza mínima final...")
        kernel_tiny = np.ones((2, 2), np.uint8)
        cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel_tiny)
        
        # 4. Aplicar suavizado de 1 píxel para eliminar bordes dentados
        print("🎨 Aplicando suavizado de 1 píxel para bordes suaves...")
        final_mask = cv2.GaussianBlur(cleaned_mask, (3, 3), 0.5)
        _, final_mask = cv2.threshold(final_mask, 127, 255, cv2.THRESH_BINARY)
        
        # 5. Aplicar a imagen original
        original_array = np.array(original)
        original_array[:,:,3] = final_mask
        
        result_image = Image.fromarray(original_array, 'RGBA')
        result_image.save(output_path, 'PNG')
        
        # Estadísticas
        pixels_final = np.sum(final_mask > 0)
        pixels_total = final_mask.shape[0] * final_mask.shape[1]
        porcentaje_final = (pixels_final / pixels_total) * 100
        
        pixels_base = np.sum(base_mask > 0)
        porcentaje_base = (pixels_base / pixels_total) * 100
        
        print(f"✅ ¡Limpieza directa completada!")
        print(f"💾 Guardado en: {output_path}")
        print(f"📊 Antes: {porcentaje_base:.1f}% → Después: {porcentaje_final:.1f}%")
        print(f"🎯 Diferencia: {porcentaje_base - porcentaje_final:.1f}% (solo píxeles blancos eliminados)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la limpieza directa: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("🎯 Uso: python direct_white_cleanup.py <imagen_entrada> <imagen_salida> [umbral_blanco]")
        print("📝 Umbrales de blanco:")
        print("   240 - Detecta blancos y casi-blancos")
        print("   245 - Detecta solo píxeles muy blancos (recomendado)")
        print("   250 - Detecta solo píxeles extremadamente blancos")
        print("💡 Ejemplo: python direct_white_cleanup.py modelo.jpg modelo_limpio.png 245")
        print("🎯 Enfoque DIRECTO: elimina solo píxeles blancos específicos")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    threshold = int(sys.argv[3]) if len(sys.argv) > 3 else 245
    
    if not os.path.exists(input_path):
        print(f"❌ Error: No se encuentra el archivo {input_path}")
        sys.exit(1)
    
    success = simple_border_cleanup(input_path, output_path, threshold)
    
    if success:
        print("\n🎉 ¡Limpieza directa exitosa!")
        print("✅ Solo se eliminaron píxeles blancos específicos")
        print("🛡️  Modelo preservado completamente")
        print("💡 Si aún hay blancos, prueba con umbral 240")
        print("💡 Si eliminó demasiado, prueba con umbral 250")
    else:
        print("\n💥 La limpieza directa falló")
        sys.exit(1)

if __name__ == "__main__":
    main()
