#!/usr/bin/env python3
"""
Background Remover usando ISNet - Versión Definitiva
===================================================

Solución optimizada para eliminar fondos de avatares y modelos complejos.
Utiliza ISNet-General-Use que mantiene la integridad de figuras completas
a diferencia de U²-Net que puede fragmentar modelos complejos.

Características:
- Segmentación completa con ISNet-General-Use
- Eliminación de píxeles blancos residuales  
- Suavizado de bordes para evitar dentado
- Conexión de componentes para mantener unidad del modelo

Uso:
    python bg_remover.py input.png output.png [verbose]
    
Ejemplos:
    python bg_remover.py avatar.jpg resultado.png
    python bg_remover.py modelo.png limpio.png true
"""

import cv2
import numpy as np
from rembg import remove, new_session
from PIL import Image
import sys
import os
import io
from scipy import ndimage


def remove_background_isnet(input_path, output_path, verbose=False):
    """
    Elimina el fondo usando ISNet con procesamiento optimizado.
    
    Args:
        input_path (str): Ruta de la imagen de entrada
        output_path (str): Ruta de la imagen de salida
        verbose (bool): Mostrar información detallada del proceso
    
    Returns:
        bool: True si el proceso fue exitoso
    """
    try:
        if verbose:
            print(f"📸 Cargando imagen: {input_path}")
        
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
            # Calcular estadísticas
            original_pixels = img_array.shape[0] * img_array.shape[1]
            alpha_channel = result_array[:,:,3] 
            visible_pixels = np.sum(alpha_channel > 0)
            percentage = (visible_pixels / original_pixels) * 100
            print(f"📊 Píxeles capturados: {percentage:.1f}% ({visible_pixels:,}/{original_pixels:,})")
        
        # Conectar componentes pequeños al componente principal
        if verbose:
            print("🔗 Conectando componentes...")
        result_array = connect_components(result_array)
        
        # Limpiar píxeles blancos residuales
        if verbose:
            print("🧹 Eliminando píxeles blancos residuales...")
        result_array = remove_white_pixels(result_array)
        
        # Aplicar suavizado suave a los bordes
        if verbose:
            print("✨ Aplicando suavizado de bordes...")
        result_array = smooth_edges(result_array)
        
        # Guardar resultado
        result_final = Image.fromarray(result_array)
        result_final.save(output_path, format='PNG')
        
        if verbose:
            print(f"✅ Imagen procesada guardada en: {output_path}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {str(e)}")
        return False


def connect_components(img_array):
    """Conecta componentes pequeños al componente principal."""
    alpha = img_array[:,:,3]
    
    # Encontrar componentes conectados
    binary = (alpha > 0).astype(np.uint8)
    num_labels, labels = cv2.connectedComponents(binary)
    
    if num_labels <= 2:  # Solo fondo + un componente
        return img_array
    
    # Encontrar el componente más grande (excluyendo el fondo)
    component_sizes = []
    for i in range(1, num_labels):
        size = np.sum(labels == i)
        component_sizes.append((size, i))
    
    # Ordenar por tamaño
    component_sizes.sort(reverse=True)
    main_component_label = component_sizes[0][1]
    
    # Crear kernel para dilatación
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    
    # Expandir componente principal
    main_mask = (labels == main_component_label).astype(np.uint8)
    expanded_main = cv2.dilate(main_mask, kernel, iterations=2)
    
    # Conectar componentes pequeños que estén cerca
    for size, label in component_sizes[1:]:
        if size < 1000:  # Solo componentes pequeños
            component_mask = (labels == label).astype(np.uint8)
            # Si hay intersección después de la dilatación, incluir
            if np.any(expanded_main & component_mask):
                main_mask = main_mask | component_mask
    
    # Aplicar la máscara conectada
    result = img_array.copy()
    alpha_connected = alpha * main_mask
    result[:,:,3] = alpha_connected
    
    return result


def remove_white_pixels(img_array):
    """Elimina píxeles blancos o casi blancos del resultado."""
    result = img_array.copy()
    alpha = result[:,:,3]
    
    # Solo procesar píxeles visibles
    visible_mask = alpha > 0
    if not np.any(visible_mask):
        return result
    
    # Calcular luminosidad para píxeles visibles
    rgb = result[:,:,:3]
    luminosity = np.zeros_like(alpha, dtype=np.float32)
    luminosity[visible_mask] = 0.299 * rgb[visible_mask,0] + 0.587 * rgb[visible_mask,1] + 0.114 * rgb[visible_mask,2]
    
    # Umbral adaptativo basado en la distribución
    valid_luminosity = luminosity[visible_mask]
    if len(valid_luminosity) > 0:
        threshold = np.percentile(valid_luminosity, 95)
        threshold = max(threshold, 240)  # Mínimo conservador
        
        # Aplicar filtro de blancos
        white_mask = (luminosity > threshold) & visible_mask
        result[white_mask, 3] = 0
    
    return result


def smooth_edges(img_array):
    """Aplica suavizado suave a los bordes para evitar dentado."""
    result = img_array.copy()
    alpha = result[:,:,3].astype(np.float32)
    
    # Aplicar Gaussian blur muy suave solo al canal alfa
    alpha_smooth = cv2.GaussianBlur(alpha, (3, 3), 0.5)
    
    # Mantener los píxeles completamente opacos
    strong_alpha_mask = alpha == 255
    alpha_smooth[strong_alpha_mask] = 255
    
    result[:,:,3] = alpha_smooth.astype(np.uint8)
    return result


def main():
    """Función principal del script."""
    if len(sys.argv) < 3:
        print("Uso: python bg_remover.py <imagen_entrada> <imagen_salida> [verbose]")
        print("\nEjemplos:")
        print("  python bg_remover.py avatar.jpg resultado.png")
        print("  python bg_remover.py modelo.png limpio.png true")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    verbose = len(sys.argv) > 3 and sys.argv[3].lower() in ['true', '1', 'yes', 'v']
    
    print("🎨 Background Remover ISNet - Versión Definitiva")
    print("=" * 50)
    
    success = remove_background_isnet(input_path, output_path, verbose)
    
    if success:
        print("\n🎉 Proceso completado exitosamente!")
    else:
        print("\n💥 Error durante el procesamiento")
        sys.exit(1)


if __name__ == "__main__":
    main()
