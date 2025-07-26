#!/usr/bin/env python3
"""
Recorte conservador uniforme - Elimina mínimamente pero de forma simétrica
Basado en modelo_balanceado pero con ajuste uniforme muy suave
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

def gentle_uniform_trim(mask, trim_pixels=2):
    """
    Aplica recorte muy suave y uniforme usando kernel circular pequeño
    """
    # Kernel circular muy pequeño para uniformidad
    kernel_size = max(3, trim_pixels * 2 + 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    
    # Erosión muy suave con una sola iteración
    trimmed_mask = cv2.erode(mask, kernel, iterations=1)
    
    # Cerrar pequeños huecos que puedan haberse creado
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    trimmed_mask = cv2.morphologyEx(trimmed_mask, cv2.MORPH_CLOSE, kernel_close)
    
    return trimmed_mask

def conservative_uniform_border_removal(input_path, output_path, gentle_trim=True):
    """
    Elimina borde blanco de manera muy conservadora pero uniforme
    
    Args:
        input_path: Imagen de entrada
        output_path: Imagen de salida
        gentle_trim: Si True, aplica recorte muy suave
    """
    try:
        print("🎯 Recorte CONSERVADOR UNIFORME...")
        print("🛡️  Máxima preservación del modelo")
        
        # Cargar imagen
        with Image.open(input_path) as img:
            original = img.convert('RGBA')
            original_rgb = img.convert('RGB')
            print(f"📐 Procesando: {original.size}")
        
        # 1. Generar máscara base igual que modelo_balanceado
        print("🤖 Generando máscara conservadora...")
        session = new_session('u2net_human_seg')
        ai_result = remove(original_rgb, session=session)
        base_mask = np.array(ai_result)[:,:,3]
        
        # Usar el mismo threshold que modelo_balanceado
        _, base_mask = cv2.threshold(base_mask, 100, 255, cv2.THRESH_BINARY)
        
        # 2. Solo aplicar recorte muy suave si se solicita
        if gentle_trim:
            print("✂️  Aplicando recorte conservador uniforme...")
            # Recorte muy pequeño: solo 2-3 píxeles
            trimmed_mask = gentle_uniform_trim(base_mask, 2)
            
            # Si el resultado es muy diferente, usar el original
            original_pixels = np.sum(base_mask > 127)
            trimmed_pixels = np.sum(trimmed_mask > 127)
            reduction_percentage = (original_pixels - trimmed_pixels) / original_pixels * 100
            
            if reduction_percentage > 15:  # Si perdió más del 15%, usar original
                print("⚠️  Recorte excesivo detectado, usando máscara original")
                final_mask = base_mask
            else:
                final_mask = trimmed_mask
                print(f"✅ Recorte aplicado: {reduction_percentage:.1f}% de reducción")
        else:
            print("🛡️  Sin recorte - preservando máscara original")
            final_mask = base_mask
        
        # 3. Limpieza final muy suave y simétrica
        print("✨ Limpieza final simétrica...")
        
        # Solo cerrar huecos muy pequeños
        kernel_tiny = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel_tiny)
        
        # Suavizado isotrópico mínimo
        final_mask = cv2.GaussianBlur(final_mask, (3, 3), 0.3)
        _, final_mask = cv2.threshold(final_mask, 120, 255, cv2.THRESH_BINARY)
        
        # 4. Aplicar a imagen original
        original_array = np.array(original)
        original_array[:,:,3] = final_mask
        
        result_image = Image.fromarray(original_array, 'RGBA')
        result_image.save(output_path, 'PNG')
        
        # Estadísticas
        pixels_modelo = np.sum(final_mask > 127)
        pixels_total = final_mask.shape[0] * final_mask.shape[1]
        porcentaje = (pixels_modelo / pixels_total) * 100
        
        print(f"✅ ¡Recorte conservador uniforme completado!")
        print(f"💾 Guardado en: {output_path}")
        print(f"📊 Modelo conservador: {porcentaje:.1f}% de la imagen")
        print("🛡️  Modelo preservado con uniformidad garantizada")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el recorte conservador: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("🎯 Uso: python conservative_uniform.py <imagen_entrada> <imagen_salida> [aplicar_recorte]")
        print("📝 Opciones:")
        print("   true   - Aplicar recorte muy suave y uniforme")
        print("   false  - Solo aplicar limpieza uniforme sin recorte")
        print("💡 Ejemplo: python conservative_uniform.py modelo.jpg modelo_conservador.png true")
        print("🛡️  Diseñado para preservar modelo como modelo_balanceado pero uniformemente")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    apply_trim = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else True
    
    if not os.path.exists(input_path):
        print(f"❌ Error: No se encuentra el archivo {input_path}")
        sys.exit(1)
    
    success = conservative_uniform_border_removal(input_path, output_path, apply_trim)
    
    if success:
        print("\n🎉 ¡Procesamiento conservador uniforme exitoso!")
        print("✅ Modelo preservado con tratamiento simétrico")
        print("🛡️  Calidad similar a modelo_balanceado pero sin asimetrías")
    else:
        print("\n💥 El procesamiento falló")
        sys.exit(1)

if __name__ == "__main__":
    main()
