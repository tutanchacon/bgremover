#!/usr/bin/env python3
"""
Eliminación de fondo para avatares humanos con bordes super definidos
Especializado para obtener bordes nítidos y precisos en avatares de personas
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session
from scipy.ndimage import binary_erosion, binary_dilation

def sharpen_edges(mask, iterations=2):
    """Afila los bordes de la máscara para mayor definición"""
    # Convertir a binario si no lo está
    if mask.dtype != np.uint8:
        mask = (mask * 255).astype(np.uint8)
    
    # Crear kernel para operaciones morfológicas
    kernel_small = np.ones((3,3), np.uint8)
    kernel_medium = np.ones((5,5), np.uint8)
    
    # Erosión seguida de dilatación para limpiar bordes
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_small)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_small)
    
    # Aplicar filtro bilateral para suavizar manteniendo bordes
    mask = cv2.bilateralFilter(mask, 9, 75, 75)
    
    # Aplicar threshold para bordes más definidos
    _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    
    return mask

def enhance_human_detection(image):
    """Mejora la detección específica para humanos"""
    # Convertir a array numpy si es PIL
    if isinstance(image, Image.Image):
        img_array = np.array(image)
    else:
        img_array = image
    
    # Aplicar slight blur para reducir ruido antes del procesamiento
    img_array = cv2.GaussianBlur(img_array, (3, 3), 0.5)
    
    # Aumentar ligeramente el contraste para mejor detección
    img_array = cv2.convertScaleAbs(img_array, alpha=1.1, beta=10)
    
    return Image.fromarray(img_array)

def refine_human_mask(mask, original_size):
    """Refina la máscara específicamente para siluetas humanas"""
    # Redimensionar mask si es necesario
    if mask.shape[:2] != original_size[:2]:
        mask = cv2.resize(mask, (original_size[1], original_size[0]), interpolation=cv2.INTER_LINEAR)
    
    # Crear kernel específico para forma humana
    kernel_vertical = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 7))
    kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 3))
    
    # Operaciones morfológicas para preservar la forma humana
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_vertical)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_horizontal)
    
    # Eliminar pequeños holes en el cuerpo
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    
    # Suavizar bordes manteniendo la definición
    mask = cv2.medianBlur(mask, 5)
    
    return mask

def remove_background_sharp_human(input_path, output_path, edge_strength='high'):
    """
    Remueve fondo de avatar humano con bordes super definidos
    
    Args:
        input_path: Ruta de imagen de entrada
        output_path: Ruta de imagen de salida
        edge_strength: 'low', 'medium', 'high', 'ultra' para diferentes niveles de definición
    """
    try:
        print("🤖 Iniciando procesamiento de avatar humano...")
        
        # Cargar imagen original
        with Image.open(input_path) as img:
            original = img.convert('RGBA')
            original_size = original.size
            print(f"📐 Tamaño original: {original_size}")
        
        # Crear sesión específica para humanos
        print("🧠 Creando sesión U²-Net para humanos...")
        session = new_session('u2net_human_seg')
        
        # Mejorar imagen para mejor detección
        enhanced_img = enhance_human_detection(original.convert('RGB'))
        
        # Remover fondo con modelo especializado en humanos
        print("✂️  Procesando con modelo especializado en humanos...")
        result = remove(enhanced_img, session=session)
        
        # Extraer canal alpha como máscara
        mask = np.array(result)[:,:,3]
        
        # Refinar máscara para forma humana
        print("🎯 Refinando máscara para silueta humana...")
        mask = refine_human_mask(mask, np.array(original).shape)
        
        # Aplicar diferentes niveles de definición de bordes
        edge_iterations = {
            'low': 1,
            'medium': 2, 
            'high': 3,
            'ultra': 4
        }
        
        iterations = edge_iterations.get(edge_strength, 3)
        print(f"🔪 Aplicando bordes definidos (nivel: {edge_strength})...")
        
        # Afinar bordes según el nivel seleccionado
        mask = sharpen_edges(mask, iterations)
        
        # Para nivel ultra, aplicar processing adicional
        if edge_strength == 'ultra':
            # Aplicar unsharp mask para bordes extra nítidos
            gaussian = cv2.GaussianBlur(mask, (0, 0), 2.0)
            mask = cv2.addWeighted(mask, 1.5, gaussian, -0.5, 0)
            mask = np.clip(mask, 0, 255).astype(np.uint8)
            
            # Threshold final para bordes perfectamente definidos
            _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)
        
        # Aplicar máscara a imagen original
        original_array = np.array(original)
        
        # Asegurar que la máscara tenga la misma dimensión
        if len(mask.shape) == 2:
            mask = np.stack([mask] * 3 + [mask], axis=2)
        
        # Normalizar máscara
        mask_normalized = mask.astype(float) / 255.0
        
        # Aplicar máscara
        result_array = original_array.copy()
        result_array[:,:,3] = (mask_normalized[:,:,3] * 255).astype(np.uint8)
        
        # Crear imagen final
        final_result = Image.fromarray(result_array, 'RGBA')
        
        # Guardar resultado
        final_result.save(output_path, 'PNG')
        
        print(f"✅ ¡Éxito! Avatar procesado con bordes {edge_strength}")
        print(f"💾 Guardado en: {output_path}")
        print("🎭 Optimizado específicamente para avatares humanos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("🎯 Uso: python sharp_human_avatar.py <imagen_entrada> <imagen_salida> [nivel_bordes]")
        print("📝 Niveles de bordes: low, medium, high, ultra")
        print("💡 Ejemplo: python sharp_human_avatar.py avatar.jpg avatar_sharp.png ultra")
        print("🤖 Especializado para avatares humanos con bordes súper definidos")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    edge_level = sys.argv[3] if len(sys.argv) > 3 else 'high'
    
    if not os.path.exists(input_path):
        print(f"❌ Error: No se encuentra el archivo {input_path}")
        sys.exit(1)
    
    success = remove_background_sharp_human(input_path, output_path, edge_level)
    
    if success:
        print("\n🎉 ¡Procesamiento completado exitosamente!")
        print("💡 Para bordes aún más definidos, prueba con el nivel 'ultra'")
    else:
        print("\n💥 El procesamiento falló")
        sys.exit(1)

if __name__ == "__main__":
    main()
