#!/usr/bin/env python3
"""
Segmentación mejorada para modelos completos
Enfoque específico para capturar personajes completos con todos sus detalles
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

def improved_model_segmentation(original_image):
    """
    Segmentación mejorada que captura mejor los modelos completos
    """
    img_array = np.array(original_image)
    
    # 1. Probar múltiples modelos y combinar resultados
    models_to_try = ['u2net_human_seg', 'u2net', 'silueta']
    masks = []
    
    print("🤖 Probando múltiples modelos de segmentación...")
    
    for model_name in models_to_try:
        try:
            print(f"   🔍 Probando modelo: {model_name}")
            session = new_session(model_name)
            result = remove(original_image, session=session)
            mask = np.array(result)[:,:,3]
            
            # Normalizar máscara
            if mask.max() > 0:
                mask = (mask * 255 / mask.max()).astype(np.uint8)
                masks.append(mask)
                
                pixels_captured = np.sum(mask > 127)
                total_pixels = mask.shape[0] * mask.shape[1]
                percentage = (pixels_captured / total_pixels) * 100
                print(f"      📊 {model_name}: {percentage:.1f}% capturado")
            
        except Exception as e:
            print(f"      ❌ Error con {model_name}: {e}")
            continue
    
    if not masks:
        raise Exception("No se pudo generar ninguna máscara")
    
    # 2. Combinar máscaras usando unión (OR)
    print("🔗 Combinando resultados de múltiples modelos...")
    combined_mask = np.zeros_like(masks[0])
    
    for mask in masks:
        # Redimensionar si es necesario
        if mask.shape != combined_mask.shape:
            mask = cv2.resize(mask, (combined_mask.shape[1], combined_mask.shape[0]))
        
        # Aplicar threshold conservador a cada máscara
        _, mask_binary = cv2.threshold(mask, 100, 255, cv2.THRESH_BINARY)
        
        # Combinar usando OR (tomar el máximo)
        combined_mask = cv2.bitwise_or(combined_mask, mask_binary)
    
    return combined_mask

def enhance_model_completeness(original_image, base_mask):
    """
    Mejora la completitud del modelo detectando partes que puedan haberse perdido
    """
    img_array = np.array(original_image)
    
    # 1. Análisis de conectividad para encontrar componentes separados
    print("🔍 Analizando componentes del modelo...")
    
    # Encontrar componentes conectados
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(base_mask, connectivity=8)
    
    print(f"   📊 Encontrados {num_labels-1} componentes separados")
    
    # 2. Si hay múltiples componentes grandes, intentar conectarlos
    if num_labels > 2:  # Más de 1 componente (0 es fondo)
        enhanced_mask = base_mask.copy()
        
        # Identificar componentes significativos (> 1% de la imagen)
        min_area = (base_mask.shape[0] * base_mask.shape[1]) * 0.01
        significant_components = []
        
        for i in range(1, num_labels):  # Saltar el fondo (0)
            area = stats[i, cv2.CC_STAT_AREA]
            if area > min_area:
                significant_components.append(i)
                print(f"      🎯 Componente {i}: {area} píxeles")
        
        # 3. Conectar componentes cercanos
        if len(significant_components) > 1:
            print("🔗 Conectando componentes separados...")
            
            # Dilatar cada componente para intentar conectarlos
            kernel_connect = np.ones((15, 15), np.uint8)
            dilated_mask = cv2.dilate(base_mask, kernel_connect, iterations=2)
            
            # Cerrar gaps entre componentes
            kernel_close = np.ones((25, 25), np.uint8)
            enhanced_mask = cv2.morphologyEx(dilated_mask, cv2.MORPH_CLOSE, kernel_close)
            
            # Erosionar de vuelta, pero menos que la dilatación original
            kernel_erode = np.ones((10, 10), np.uint8)
            enhanced_mask = cv2.erode(enhanced_mask, kernel_erode, iterations=1)
        else:
            enhanced_mask = base_mask
    else:
        enhanced_mask = base_mask
    
    return enhanced_mask

def detect_missing_parts(original_image, current_mask):
    """
    Detecta partes del modelo que pueden haberse perdido en la segmentación
    """
    img_array = np.array(original_image)
    
    # 1. Detectar regiones con colores similares al modelo
    print("🎨 Detectando regiones con colores similares...")
    
    # Obtener colores promedio de las áreas ya segmentadas
    masked_pixels = img_array[current_mask > 0]
    
    if len(masked_pixels) == 0:
        return current_mask
    
    # Calcular colores promedio
    mean_colors = np.mean(masked_pixels, axis=0)
    std_colors = np.std(masked_pixels, axis=0)
    
    # 2. Buscar píxeles con colores similares en el resto de la imagen
    color_similarity_mask = np.zeros(current_mask.shape, dtype=np.uint8)
    
    for c in range(3):  # RGB
        lower_bound = max(0, mean_colors[c] - 2 * std_colors[c])
        upper_bound = min(255, mean_colors[c] + 2 * std_colors[c])
        
        channel_mask = (img_array[:,:,c] >= lower_bound) & (img_array[:,:,c] <= upper_bound)
        
        if c == 0:
            color_similarity_mask = channel_mask.astype(np.uint8) * 255
        else:
            color_similarity_mask = cv2.bitwise_and(color_similarity_mask, 
                                                   channel_mask.astype(np.uint8) * 255)
    
    # 3. Filtrar por proximidad al modelo existente
    # Dilatar máscara actual para crear zona de búsqueda
    kernel_search = np.ones((30, 30), np.uint8)
    search_area = cv2.dilate(current_mask, kernel_search, iterations=1)
    
    # Solo considerar píxeles similares en la zona de búsqueda
    potential_parts = cv2.bitwise_and(color_similarity_mask, search_area)
    
    # 4. Combinar con máscara original
    enhanced_mask = cv2.bitwise_or(current_mask, potential_parts)
    
    return enhanced_mask

def complete_model_segmentation(input_path, output_path):
    """
    Segmentación completa mejorada para modelos complejos
    """
    try:
        print("🎯 Segmentación COMPLETA mejorada para modelos...")
        print("🎭 Optimizada para personajes con múltiples elementos")
        
        # Cargar imagen
        with Image.open(input_path) as img:
            original = img.convert('RGBA')
            original_rgb = img.convert('RGB')
            print(f"📐 Procesando: {original.size}")
        
        # 1. Segmentación mejorada con múltiples modelos
        base_mask = improved_model_segmentation(original_rgb)
        
        pixels_base = np.sum(base_mask > 0)
        total_pixels = base_mask.shape[0] * base_mask.shape[1]
        percentage_base = (pixels_base / total_pixels) * 100
        print(f"📊 Segmentación base: {percentage_base:.1f}%")
        
        # 2. Mejorar completitud conectando componentes
        enhanced_mask = enhance_model_completeness(original_rgb, base_mask)
        
        pixels_enhanced = np.sum(enhanced_mask > 0)
        percentage_enhanced = (pixels_enhanced / total_pixels) * 100
        print(f"📊 Después de conectar componentes: {percentage_enhanced:.1f}%")
        
        # 3. Detectar partes faltantes
        complete_mask = detect_missing_parts(original_rgb, enhanced_mask)
        
        pixels_complete = np.sum(complete_mask > 0)
        percentage_complete = (pixels_complete / total_pixels) * 100
        print(f"📊 Después de detectar partes faltantes: {percentage_complete:.1f}%")
        
        # 4. Limpieza final conservadora
        print("✨ Limpieza final...")
        
        # Solo cerrar huecos pequeños
        kernel_clean = np.ones((5, 5), np.uint8)
        final_mask = cv2.morphologyEx(complete_mask, cv2.MORPH_CLOSE, kernel_clean)
        
        # Suavizado muy ligero
        final_mask = cv2.GaussianBlur(final_mask, (3, 3), 0.5)
        _, final_mask = cv2.threshold(final_mask, 127, 255, cv2.THRESH_BINARY)
        
        # 5. Eliminar píxeles blancos específicos
        print("🧹 Eliminando píxeles blancos residuales...")
        img_array = np.array(original_rgb)
        is_white = np.all(img_array >= 245, axis=2)
        white_in_mask = (final_mask > 0) & is_white
        final_mask[white_in_mask] = 0
        
        removed_whites = np.sum(white_in_mask)
        print(f"🔍 Eliminados {removed_whites} píxeles blancos")
        
        # 6. Aplicar a imagen original
        original_array = np.array(original)
        original_array[:,:,3] = final_mask
        
        result_image = Image.fromarray(original_array, 'RGBA')
        result_image.save(output_path, 'PNG')
        
        # Estadísticas finales
        pixels_final = np.sum(final_mask > 0)
        percentage_final = (pixels_final / total_pixels) * 100
        
        print(f"✅ ¡Segmentación completa exitosa!")
        print(f"💾 Guardado en: {output_path}")
        print(f"📊 Resultado final: {percentage_final:.1f}% de la imagen")
        print(f"🎯 Mejora: {percentage_final - percentage_base:.1f}% adicional capturado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante segmentación completa: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("🎯 Uso: python improved_segmentation.py <imagen_entrada> <imagen_salida>")
        print("🎭 Especializado para modelos/personajes complejos con múltiples elementos")
        print("💡 Ejemplo: python improved_segmentation.py personaje.jpg personaje_completo.png")
        print("🤖 Usa múltiples modelos AI y técnicas de completitud")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    if not os.path.exists(input_path):
        print(f"❌ Error: No se encuentra el archivo {input_path}")
        sys.exit(1)
    
    success = complete_model_segmentation(input_path, output_path)
    
    if success:
        print("\n🎉 ¡Segmentación completa exitosa!")
        print("✅ Modelo completo capturado con múltiples técnicas")
        print("🎭 Optimizado para personajes complejos")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
