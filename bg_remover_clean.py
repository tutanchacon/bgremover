#!/usr/bin/env python3
"""
Background Remover con Control de Transparencias - Versión Mejorada
==================================================================

Solución optimizada que elimina las zonas semi-transparentes problemáticas
que pueden aparecer en objetos como globos, relojes, etc. alrededor del avatar.

Problemas que resuelve:
- Objetos semi-transparentes no deseados (globos, relojes, decoraciones)
- Áreas con alpha parcial que deberían ser completamente transparentes
- Bordes dudosos que el modelo AI no segmenta claramente

Uso:
    python bg_remover_clean.py input.png output.png [umbral_alpha] [verbose]
    
Ejemplos:
    python bg_remover_clean.py avatar.jpg limpio.png
    python bg_remover_clean.py imagen.png resultado.png 180 true
"""

import cv2
import numpy as np
from rembg import remove, new_session
from PIL import Image
import sys
import os
import io
from scipy import ndimage


def remove_background_clean(input_path, output_path, alpha_threshold=150, verbose=False):
    """
    Elimina el fondo con control estricto de transparencias semi-parciales.
    
    Args:
        input_path (str): Ruta de la imagen de entrada
        output_path (str): Ruta de la imagen de salida
        alpha_threshold (int): Umbral para eliminar transparencias parciales (0-255)
        verbose (bool): Mostrar información detallada del proceso
    
    Returns:
        bool: True si el proceso fue exitoso
    """
    try:
        if verbose:
            print(f"📸 Cargando imagen: {input_path}")
            print(f"🎯 Umbral de transparencia: {alpha_threshold}")
        
        # Verificar que el archivo existe
        if not os.path.exists(input_path):
            print(f"❌ Error: No se encuentra el archivo {input_path}")
            return False
        
        # Crear sesión ISNet
        if verbose:
            print("🤖 Inicializando modelo ISNet-General-Use...")
        session = new_session('isnet-general-use')
        
        # Cargar y procesar imagen
        with open(input_path, 'rb') as input_file:
            input_data = input_file.read()
            
        if verbose:
            print("🎯 Aplicando segmentación ISNet...")
        output_data = remove(input_data, session=session)
        
        # Convertir a imagen PIL y luego a array numpy
        img_pil = Image.open(input_path).convert('RGBA')
        result_pil = Image.open(io.BytesIO(output_data))
        
        # Convertir a arrays numpy para procesamiento
        img_array = np.array(img_pil)
        result_array = np.array(result_pil)
        
        if verbose:
            # Calcular estadísticas iniciales
            original_pixels = img_array.shape[0] * img_array.shape[1]
            alpha_channel = result_array[:,:,3] 
            visible_pixels_initial = np.sum(alpha_channel > 0)
            percentage_initial = (visible_pixels_initial / original_pixels) * 100
            print(f"📊 Píxeles iniciales: {percentage_initial:.1f}% ({visible_pixels_initial:,}/{original_pixels:,})")
        
        # PASO 1: Limpiar transparencias parciales problemáticas
        if verbose:
            print(f"🧹 Eliminando transparencias < {alpha_threshold}...")
        result_array = clean_partial_transparencies(result_array, alpha_threshold, verbose)
        
        # PASO 2: Conectar componentes principales
        if verbose:
            print("🔗 Conectando componentes principales...")
        result_array = connect_main_components(result_array, verbose)
        
        # PASO 3: Limpiar píxeles blancos residuales
        if verbose:
            print("🎨 Eliminando píxeles blancos residuales...")
        result_array = remove_white_pixels_advanced(result_array)
        
        # PASO 4: Aplicar suavizado final conservador
        if verbose:
            print("✨ Aplicando suavizado final...")
        result_array = smooth_edges_conservative(result_array)
        
        # Estadísticas finales
        if verbose:
            alpha_final = result_array[:,:,3]
            visible_final = np.sum(alpha_final > 0)
            percentage_final = (visible_final / original_pixels) * 100
            reduction = percentage_initial - percentage_final
            print(f"📈 Píxeles finales: {percentage_final:.1f}% ({visible_final:,}/{original_pixels:,})")
            print(f"📉 Reducción: -{reduction:.1f}% (eliminó transparencias problemáticas)")
        
        # Guardar resultado
        result_final = Image.fromarray(result_array)
        result_final.save(output_path, format='PNG')
        
        if verbose:
            print(f"✅ Imagen limpia guardada en: {output_path}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {str(e)}")
        return False


def clean_partial_transparencies(img_array, threshold, verbose=False):
    """
    Elimina transparencias parciales que causan objetos semi-transparentes no deseados.
    """
    result = img_array.copy()
    alpha = result[:,:,3]
    
    # Contar píxeles en diferentes rangos de transparencia
    if verbose:
        total_pixels = alpha.shape[0] * alpha.shape[1]
        transparent = np.sum(alpha == 0)
        partial = np.sum((alpha > 0) & (alpha < threshold))
        solid = np.sum(alpha >= threshold)
        
        print(f"   🔍 Análisis alpha:")
        print(f"   - Transparente (0): {(transparent/total_pixels)*100:.1f}%")
        print(f"   - Parcial (1-{threshold-1}): {(partial/total_pixels)*100:.1f}% ← PROBLEMA")
        print(f"   - Sólido ({threshold}+): {(solid/total_pixels)*100:.1f}%")
    
    # Eliminar píxeles con transparencia parcial problemática
    # Estos suelen ser objetos como globos, relojes, etc. que el modelo ve como "dudosos"
    problematic_mask = (alpha > 0) & (alpha < threshold)
    result[problematic_mask, 3] = 0  # Hacer completamente transparentes
    
    # Para píxeles que están por encima del umbral, asegurar que sean completamente opacos
    solid_mask = alpha >= threshold
    result[solid_mask, 3] = 255
    
    if verbose:
        eliminated = np.sum(problematic_mask)
        print(f"   ❌ Eliminados {eliminated:,} píxeles semi-transparentes")
    
    return result


def connect_main_components(img_array, verbose=False):
    """
    Conecta solo los componentes principales, eliminando fragmentos pequeños.
    """
    alpha = img_array[:,:,3]
    
    # Encontrar componentes conectados
    binary = (alpha > 0).astype(np.uint8)
    num_labels, labels = cv2.connectedComponents(binary)
    
    if num_labels <= 2:  # Solo fondo + un componente
        return img_array
    
    # Analizar tamaños de componentes
    component_sizes = []
    for i in range(1, num_labels):
        size = np.sum(labels == i)
        component_sizes.append((size, i))
    
    # Ordenar por tamaño
    component_sizes.sort(reverse=True)
    
    if verbose:
        print(f"   🔍 Encontrados {num_labels-1} componentes:")
        for i, (size, label) in enumerate(component_sizes[:5]):  # Mostrar top 5
            percentage = (size / (alpha.shape[0] * alpha.shape[1])) * 100
            print(f"   - Componente {i+1}: {size:,} píxeles ({percentage:.2f}%)")
    
    # Mantener solo componentes principales (>1% del total)
    total_pixels = alpha.shape[0] * alpha.shape[1]
    main_components = []
    
    for size, label in component_sizes:
        percentage = (size / total_pixels) * 100
        if percentage >= 1.0:  # Componentes >= 1% del total
            main_components.append(label)
        elif len(main_components) == 0:  # Siempre mantener al menos el más grande
            main_components.append(label)
    
    # Crear máscara solo con componentes principales
    main_mask = np.zeros_like(alpha, dtype=np.uint8)
    for label in main_components:
        main_mask[labels == label] = 1
    
    # Aplicar la máscara
    result = img_array.copy()
    result[:,:,3] = alpha * main_mask
    
    if verbose:
        kept = len(main_components)
        eliminated = (num_labels - 1) - kept
        print(f"   ✅ Mantenidos {kept} componentes principales")
        print(f"   ❌ Eliminados {eliminated} componentes pequeños")
    
    return result


def remove_white_pixels_advanced(img_array):
    """
    Eliminación avanzada de píxeles blancos con detección de contexto.
    """
    result = img_array.copy()
    alpha = result[:,:,3]
    
    # Solo procesar píxeles visibles
    visible_mask = alpha > 0
    if not np.any(visible_mask):
        return result
    
    rgb = result[:,:,:3]
    
    # Calcular luminosidad solo para píxeles visibles
    luminosity = np.zeros_like(alpha, dtype=np.float32)
    luminosity[visible_mask] = 0.299 * rgb[visible_mask,0] + 0.587 * rgb[visible_mask,1] + 0.114 * rgb[visible_mask,2]
    
    # Calcular saturación para distinguir blancos verdaderos de colores claros
    saturation = np.zeros_like(alpha, dtype=np.float32)
    for y in range(rgb.shape[0]):
        for x in range(rgb.shape[1]):
            if visible_mask[y,x]:
                r, g, b = rgb[y,x,0], rgb[y,x,1], rgb[y,x,2]
                max_val = max(r, g, b)
                min_val = min(r, g, b)
                if max_val > 0:
                    saturation[y,x] = (max_val - min_val) / max_val
    
    # Definir píxeles blancos como: alta luminosidad Y baja saturación
    white_threshold_lum = 235  # Umbral de luminosidad
    white_threshold_sat = 0.15  # Umbral de saturación (baja = más blanco)
    
    white_mask = (luminosity > white_threshold_lum) & (saturation < white_threshold_sat) & visible_mask
    result[white_mask, 3] = 0
    
    return result


def smooth_edges_conservative(img_array):
    """
    Suavizado conservador que preserva los bordes nítidos del avatar principal.
    """
    result = img_array.copy()
    alpha = result[:,:,3].astype(np.float32)
    
    # Aplicar blur muy suave solo en los bordes
    alpha_blurred = cv2.GaussianBlur(alpha, (3, 3), 0.3)  # Sigma más pequeño
    
    # Mantener píxeles completamente opacos sin cambios
    strong_alpha_mask = alpha == 255
    alpha_blurred[strong_alpha_mask] = 255
    
    # Para píxeles de borde (no completamente opacos), aplicar blend conservador
    edge_mask = (alpha > 0) & (alpha < 255)
    blend_factor = 0.3  # Mezcla conservadora
    alpha[edge_mask] = (1 - blend_factor) * alpha[edge_mask] + blend_factor * alpha_blurred[edge_mask]
    
    result[:,:,3] = alpha.astype(np.uint8)
    return result


def main():
    """Función principal del script."""
    if len(sys.argv) < 3:
        print("Uso: python bg_remover_clean.py <imagen_entrada> <imagen_salida> [umbral_alpha] [verbose]")
        print("\nEjemplos:")
        print("  python bg_remover_clean.py avatar.jpg resultado.png")
        print("  python bg_remover_clean.py imagen.png limpia.png 180 true")
        print("\nUmbral alpha (opcional):")
        print("  - 100-130: Muy agresivo (elimina más objetos dudosos)")
        print("  - 150: Balanceado (recomendado)")
        print("  - 180-200: Conservador (mantiene más detalles)")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    # Parámetros opcionales
    alpha_threshold = 150  # Valor por defecto
    if len(sys.argv) > 3 and sys.argv[3].isdigit():
        alpha_threshold = int(sys.argv[3])
        verbose_arg = 4
    else:
        verbose_arg = 3
    
    verbose = len(sys.argv) > verbose_arg and sys.argv[verbose_arg].lower() in ['true', '1', 'yes', 'v']
    
    print("🎨 Background Remover - Control de Transparencias")
    print("=" * 55)
    
    success = remove_background_clean(input_path, output_path, alpha_threshold, verbose)
    
    if success:
        print("\n🎉 Proceso completado exitosamente!")
        print("💡 Si aún quedan objetos no deseados, prueba con un umbral más bajo (100-130)")
    else:
        print("\n💥 Error durante el procesamiento")
        sys.exit(1)


if __name__ == "__main__":
    main()
