#!/usr/bin/env python3
"""
Eliminación inteligente de borde blanco SIN destruir el modelo
Preserva el modelo humano completo mientras elimina solo el halo blanco
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

def smart_white_border_removal(original_image, ai_mask, border_size=30):
    """
    Elimina el borde blanco de manera inteligente sin destruir el modelo
    
    Args:
        original_image: Imagen original RGB
        ai_mask: Máscara generada por AI
        border_size: Tamaño aproximado del borde blanco a eliminar (en píxeles)
    """
    img_array = np.array(original_image)
    
    # 1. Crear máscara base conservadora (preservar el modelo)
    base_mask = ai_mask.copy()
    _, base_mask = cv2.threshold(base_mask, 100, 255, cv2.THRESH_BINARY)
    
    # 2. Detectar regiones claramente del modelo (con color/textura)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Detectar variaciones en la imagen (texturas, sombras, etc.)
    # Esto nos ayuda a identificar partes reales del modelo
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    texture_mask = np.abs(laplacian) > 5  # Áreas con textura/detalle
    
    # 3. Detectar píxeles claramente blancos (fondo)
    # Ser muy conservador aquí - solo píxeles MUY blancos
    very_white_pixels = np.all(img_array > 245, axis=2)  # RGB > 245 = muy blanco
    
    # 4. Crear zonas de protección para el modelo
    # Dilatar la máscara de textura para proteger el modelo
    kernel_protect = np.ones((15, 15), np.uint8)
    protected_areas = cv2.dilate(texture_mask.astype(np.uint8) * 255, kernel_protect, iterations=1)
    
    # 5. Solo eliminar píxeles que sean:
    #    - Muy blancos Y
    #    - NO estén en áreas protegidas Y  
    #    - Estén cerca del borde de la máscara original
    
    # Encontrar el borde de la máscara original
    kernel_edge = np.ones((5, 5), np.uint8)
    mask_eroded = cv2.erode(base_mask, kernel_edge, iterations=border_size//5)
    border_region = base_mask - mask_eroded  # Solo la región del borde
    
    # 6. Píxeles a eliminar: muy blancos + en región de borde + no protegidos
    pixels_to_remove = (very_white_pixels & 
                       (border_region > 0) & 
                       (protected_areas == 0))
    
    # 7. Aplicar eliminación conservadora
    refined_mask = base_mask.copy()
    refined_mask[pixels_to_remove] = 0
    
    # 8. Limpiar bordes suavemente sin destruir el modelo
    kernel_smooth = np.ones((3, 3), np.uint8)
    refined_mask = cv2.morphologyEx(refined_mask, cv2.MORPH_CLOSE, kernel_smooth)
    
    # 9. Suavizar bordes muy levemente
    refined_mask = cv2.GaussianBlur(refined_mask, (3, 3), 0.5)
    
    return refined_mask

def preserve_model_details(mask, original_image):
    """Asegura que no se pierdan detalles importantes del modelo"""
    img_array = np.array(original_image)
    
    # Detectar áreas con detalles importantes (rostro, manos, etc.)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Usar detector de bordes suave para encontrar detalles
    edges = cv2.Canny(gray, 10, 30)
    
    # Dilatar los bordes para crear zonas de protección
    kernel_protect = np.ones((7, 7), np.uint8)
    detail_protection = cv2.dilate(edges, kernel_protect, iterations=1)
    
    # Asegurar que estas áreas estén incluidas en la máscara
    protected_mask = cv2.bitwise_or(mask, detail_protection)
    
    return protected_mask

def balanced_border_removal(input_path, output_path, border_treatment='smart'):
    """
    Elimina borde blanco de manera balanceada sin destruir el modelo
    
    Args:
        input_path: Ruta de imagen de entrada
        output_path: Ruta de imagen de salida
        border_treatment: 'conservative', 'smart', 'careful'
    """
    try:
        print("🎯 Eliminación INTELIGENTE de borde blanco...")
        print("🛡️  Modo: PRESERVAR MODELO COMPLETO")
        
        # Cargar imagen original
        with Image.open(input_path) as img:
            original = img.convert('RGBA')
            original_rgb = img.convert('RGB')
            print(f"📐 Procesando imagen: {original.size}")
        
        # 1. Obtener máscara conservadora con AI
        print("🤖 Creando máscara base conservadora...")
        session = new_session('u2net_human_seg')
        ai_result = remove(original_rgb, session=session)
        ai_mask = np.array(ai_result)[:,:,3]
        
        # 2. Configurar tratamiento según nivel
        border_sizes = {
            'conservative': 15,  # Solo bordes muy pequeños
            'smart': 25,         # Bordes medianos (recomendado)
            'careful': 35        # Bordes más grandes pero cuidadoso
        }
        
        border_size = border_sizes.get(border_treatment, 25)
        
        # 3. Aplicar eliminación inteligente
        print(f"🧠 Eliminación inteligente (borde ~{border_size}px)...")
        refined_mask = smart_white_border_removal(original_rgb, ai_mask, border_size)
        
        # 4. Preservar detalles del modelo
        print("🛡️  Preservando detalles del modelo...")
        final_mask = preserve_model_details(refined_mask, original_rgb)
        
        # 5. Limpiar muy suavemente
        print("✨ Limpieza suave final...")
        
        # Solo cerrar huecos pequeños DENTRO del modelo
        kernel_gentle = np.ones((5, 5), np.uint8)
        final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel_gentle)
        
        # Threshold suave para mantener transiciones
        final_mask = cv2.GaussianBlur(final_mask, (3, 3), 0.5)
        _, final_mask = cv2.threshold(final_mask, 100, 255, cv2.THRESH_BINARY)
        
        # 6. Aplicar máscara a imagen original
        original_array = np.array(original)
        original_array[:,:,3] = final_mask
        
        # 7. Crear imagen final
        result_image = Image.fromarray(original_array, 'RGBA')
        result_image.save(output_path, 'PNG')
        
        print(f"✅ ¡Modelo preservado SIN borde blanco!")
        print(f"💾 Guardado en: {output_path}")
        print(f"🎯 Tratamiento: {border_treatment}")
        
        # Estadísticas
        pixels_modelo = np.sum(final_mask > 127)
        pixels_total = final_mask.shape[0] * final_mask.shape[1]
        porcentaje = (pixels_modelo / pixels_total) * 100
        print(f"📊 Modelo preservado: {porcentaje:.1f}% de la imagen")
        print("🛡️  El modelo debe estar COMPLETO y SIN destruir")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("🎯 Uso: python balanced_border_removal.py <imagen_entrada> <imagen_salida> [tratamiento]")
        print("📝 Tratamientos disponibles:")
        print("   conservative - Eliminación muy cuidadosa (borde ~15px)")
        print("   smart        - Eliminación inteligente (borde ~25px) [RECOMENDADO]")
        print("   careful      - Eliminación cuidadosa (borde ~35px)")
        print("💡 Ejemplo: python balanced_border_removal.py modelo.jpg modelo_limpio.png smart")
        print("🛡️  Diseñado para PRESERVAR el modelo completo mientras elimina borde blanco")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    treatment = sys.argv[3] if len(sys.argv) > 3 else 'smart'
    
    if not os.path.exists(input_path):
        print(f"❌ Error: No se encuentra el archivo {input_path}")
        sys.exit(1)
    
    success = balanced_border_removal(input_path, output_path, treatment)
    
    if success:
        print("\n🎉 ¡Modelo preservado exitosamente!")
        print("✅ El modelo debe estar completo y solo sin borde blanco")
        print("💡 Si aún hay mucho borde blanco, prueba con 'careful'")
        print("💡 Si se perdieron detalles, prueba con 'conservative'")
    else:
        print("\n💥 El procesamiento falló")
        sys.exit(1)

if __name__ == "__main__":
    main()
