#!/usr/bin/env python3
"""
Background Remover con Preservación de Elementos - Versión Corregida
===================================================================

CORRECCIÓN IMPORTANTE: Los globos, relojes y elementos adicionales
SON PARTE DEL PERSONAJE y deben preservarse.

El problema NO es eliminarlos, sino que aparezcan semi-transparentes.
Esta versión CORRIGE las transparencias parciales convirtiéndolas en opacas.

Objetivo:
- Preservar TODOS los elementos del personaje (globos, relojes, etc.)
- Corregir transparencias parciales → convertir a completamente opaco
- Eliminar SOLO el fondo verdadero

Uso:
    python bg_remover_preserve.py input.png output.png [umbral_minimo] [verbose]
    
Ejemplos:
    python bg_remover_preserve.py avatar.jpg resultado.png
    python bg_remover_preserve.py imagen.png limpio.png 50 true
"""

import cv2
import numpy as np
from rembg import remove, new_session
from PIL import Image
import sys
import os
import io
from scipy import ndimage


def remove_background_preserve_elements(input_path, output_path, min_alpha_threshold=50, verbose=False):
    """
    Elimina el fondo pero PRESERVA todos los elementos del personaje,
    corrigiendo transparencias parciales a completamente opacas.
    
    Args:
        input_path (str): Ruta de la imagen de entrada
        output_path (str): Ruta de la imagen de salida
        min_alpha_threshold (int): Umbral mínimo para considerar como parte del personaje (0-255)
        verbose (bool): Mostrar información detallada del proceso
    
    Returns:
        bool: True si el proceso fue exitoso
    """
    try:
        if verbose:
            print(f"📸 Cargando imagen: {input_path}")
            print(f"🎯 Umbral mínimo para preservar elementos: {min_alpha_threshold}")
        
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
        
        # PASO 1: Analizar distribución de transparencias
        if verbose:
            print("🔍 Analizando distribución de transparencias...")
        result_array = analyze_alpha_distribution(result_array, verbose)
        
        # PASO 2: Corregir transparencias parciales (convertir a opaco)
        if verbose:
            print(f"✨ Corrigiendo transparencias parciales (umbral mínimo: {min_alpha_threshold})...")
        result_array = fix_partial_transparencies(result_array, min_alpha_threshold, verbose)
        
        # PASO 3: Conectar elementos del personaje
        if verbose:
            print("🔗 Conectando elementos del personaje...")
        result_array = connect_character_elements(result_array, verbose)
        
        # PASO 4: Limpiar solo píxeles blancos de fondo residuales
        if verbose:
            print("🧹 Limpiando píxeles blancos de fondo...")
        result_array = remove_background_whites_only(result_array)
        
        # PASO 5: Suavizado conservador
        if verbose:
            print("🎨 Aplicando suavizado conservador...")
        result_array = smooth_edges_preserve(result_array)
        
        # Estadísticas finales
        if verbose:
            alpha_final = result_array[:,:,3]
            visible_final = np.sum(alpha_final > 0)
            percentage_final = (visible_final / original_pixels) * 100
            change = percentage_final - percentage_initial
            print(f"📈 Píxeles finales: {percentage_final:.1f}% ({visible_final:,}/{original_pixels:,})")
            if change > 0:
                print(f"📊 Incremento: +{change:.1f}% (transparencias corregidas a opacas)")
            else:
                print(f"📉 Cambio: {change:.1f}% (solo fondo eliminado)")
        
        # Guardar resultado
        result_final = Image.fromarray(result_array)
        result_final.save(output_path, format='PNG')
        
        if verbose:
            print(f"✅ Imagen con elementos preservados guardada en: {output_path}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {str(e)}")
        return False


def analyze_alpha_distribution(img_array, verbose=False):
    """
    Analiza la distribución de valores alpha para entender qué está detectando el modelo.
    """
    alpha = img_array[:,:,3]
    total_pixels = alpha.shape[0] * alpha.shape[1]
    
    if verbose:
        # Analizar rangos de transparencia
        transparent = np.sum(alpha == 0)
        very_low = np.sum((alpha > 0) & (alpha <= 50))
        low = np.sum((alpha > 50) & (alpha <= 100))
        medium = np.sum((alpha > 100) & (alpha <= 180))
        high = np.sum((alpha > 180) & (alpha < 255))
        solid = np.sum(alpha == 255)
        
        print(f"   📊 Distribución de transparencias:")
        print(f"   - Transparente (0): {(transparent/total_pixels)*100:.1f}%")
        print(f"   - Muy bajo (1-50): {(very_low/total_pixels)*100:.1f}% ← Posible ruido")
        print(f"   - Bajo (51-100): {(low/total_pixels)*100:.1f}% ← Elementos dudosos")
        print(f"   - Medio (101-180): {(medium/total_pixels)*100:.1f}% ← Elementos del personaje")
        print(f"   - Alto (181-254): {(high/total_pixels)*100:.1f}% ← Personaje principal")
        print(f"   - Sólido (255): {(solid/total_pixels)*100:.1f}% ← Núcleo del personaje")
    
    return img_array


def fix_partial_transparencies(img_array, min_threshold, verbose=False):
    """
    Corrige transparencias parciales convirtiéndolas en completamente opacas.
    Preserva TODOS los elementos que el modelo considera parte del personaje.
    """
    result = img_array.copy()
    alpha = result[:,:,3]
    
    # Contar elementos antes del procesamiento
    if verbose:
        total_pixels = alpha.shape[0] * alpha.shape[1]
        original_visible = np.sum(alpha > 0)
        partial_transparent = np.sum((alpha > 0) & (alpha < 255))
        
        print(f"   🔍 Antes del procesamiento:")
        print(f"   - Píxeles visibles: {original_visible:,} ({(original_visible/total_pixels)*100:.1f}%)")
        print(f"   - Semi-transparentes: {partial_transparent:,} ({(partial_transparent/total_pixels)*100:.1f}%)")
    
    # Eliminar solo ruido muy bajo (probablemente artefactos)
    noise_mask = (alpha > 0) & (alpha < min_threshold)
    result[noise_mask, 3] = 0
    
    # Convertir elementos semi-transparentes a completamente opacos
    # Estos son elementos del personaje que el modelo detectó pero con dudas
    character_elements_mask = (alpha >= min_threshold) & (alpha < 255)
    result[character_elements_mask, 3] = 255
    
    if verbose:
        noise_removed = np.sum(noise_mask)
        elements_fixed = np.sum(character_elements_mask)
        final_visible = np.sum(result[:,:,3] > 0)
        
        print(f"   ❌ Ruido eliminado: {noise_removed:,} píxeles (< {min_threshold})")
        print(f"   ✅ Elementos corregidos a opacos: {elements_fixed:,} píxeles")
        print(f"   📈 Píxeles finales visibles: {final_visible:,} ({(final_visible/total_pixels)*100:.1f}%)")
    
    return result


def connect_character_elements(img_array, verbose=False):
    """
    Conecta elementos separados que pertenecen al mismo personaje usando morfología.
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
    
    component_sizes.sort(reverse=True)
    
    if verbose:
        print(f"   🔍 Encontrados {num_labels-1} elementos separados:")
        total_pixels = alpha.shape[0] * alpha.shape[1]
        for i, (size, label) in enumerate(component_sizes[:7]):  # Mostrar top 7
            percentage = (size / total_pixels) * 100
            element_type = "Principal" if i == 0 else f"Elemento {i}"
            print(f"   - {element_type}: {size:,} píxeles ({percentage:.2f}%)")
    
    # Estrategia de conexión progresiva
    # Usar dilatación suave para conectar elementos cercanos del personaje
    kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    kernel_medium = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    
    # Dilatación progresiva para conectar elementos relacionados
    dilated = cv2.dilate(binary, kernel_small, iterations=1)
    dilated = cv2.dilate(dilated, kernel_medium, iterations=1)
    
    # Aplicar la máscara dilatada
    result = img_array.copy()
    result[:,:,3] = alpha * dilated
    
    if verbose:
        final_components = cv2.connectedComponents((result[:,:,3] > 0).astype(np.uint8))[0] - 1
        connected = num_labels - 1 - final_components
        print(f"   🔗 Elementos conectados: {connected}")
        print(f"   📊 Componentes finales: {final_components}")
    
    return result


def remove_background_whites_only(img_array):
    """
    Elimina solo píxeles blancos que claramente son fondo residual,
    preservando blancos que son parte del personaje.
    """
    result = img_array.copy()
    alpha = result[:,:,3]
    
    # Solo procesar píxeles visibles
    visible_mask = alpha > 0
    if not np.any(visible_mask):
        return result
    
    rgb = result[:,:,:3]
    
    # Calcular luminosidad y saturación
    luminosity = np.zeros_like(alpha, dtype=np.float32)
    saturation = np.zeros_like(alpha, dtype=np.float32)
    
    for y in range(rgb.shape[0]):
        for x in range(rgb.shape[1]):
            if visible_mask[y,x]:
                r, g, b = rgb[y,x,0], rgb[y,x,1], rgb[y,x,2]
                # Luminosidad
                luminosity[y,x] = 0.299 * r + 0.587 * g + 0.114 * b
                # Saturación
                max_val = max(r, g, b)
                min_val = min(r, g, b)
                if max_val > 0:
                    saturation[y,x] = (max_val - min_val) / max_val
    
    # Solo eliminar blancos muy puros que están en los bordes (probablemente fondo)
    # Ser muy conservador para no eliminar blancos del personaje
    white_threshold_lum = 245  # Muy alto - solo blancos extremos
    white_threshold_sat = 0.05  # Muy bajo - solo blancos purísimos
    
    # Detectar bordes de la imagen
    h, w = alpha.shape
    border_mask = np.zeros_like(alpha, dtype=bool)
    border_width = 10
    border_mask[:border_width, :] = True  # Top
    border_mask[-border_width:, :] = True  # Bottom
    border_mask[:, :border_width] = True  # Left
    border_mask[:, -border_width:] = True  # Right
    
    # Solo eliminar blancos puros que están cerca de los bordes
    background_white_mask = (
        (luminosity > white_threshold_lum) & 
        (saturation < white_threshold_sat) & 
        visible_mask & 
        border_mask
    )
    
    result[background_white_mask, 3] = 0
    
    return result


def smooth_edges_preserve(img_array):
    """
    Suavizado muy conservador que preserva la definición de todos los elementos.
    """
    result = img_array.copy()
    alpha = result[:,:,3].astype(np.float32)
    
    # Suavizado muy suave solo en las transiciones
    alpha_blurred = cv2.GaussianBlur(alpha, (3, 3), 0.2)  # Sigma muy pequeño
    
    # Mantener píxeles completamente opacos
    solid_mask = alpha == 255
    alpha_blurred[solid_mask] = 255
    
    # Solo aplicar suavizado en los bordes reales
    edge_mask = (alpha > 0) & (alpha < 255)
    if np.any(edge_mask):
        blend_factor = 0.15  # Muy conservador
        alpha[edge_mask] = (1 - blend_factor) * alpha[edge_mask] + blend_factor * alpha_blurred[edge_mask]
    
    result[:,:,3] = alpha.astype(np.uint8)
    return result


def main():
    """Función principal del script."""
    if len(sys.argv) < 3:
        print("Uso: python bg_remover_preserve.py <imagen_entrada> <imagen_salida> [umbral_minimo] [verbose]")
        print("\nEjemplos:")
        print("  python bg_remover_preserve.py avatar.jpg resultado.png")
        print("  python bg_remover_preserve.py imagen.png limpia.png 30 true")
        print("\nUmbral mínimo (opcional):")
        print("  - 20-30: Preserva casi todo (recomendado)")
        print("  - 50: Balanceado")
        print("  - 80-100: Más restrictivo (elimina más ruido)")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    # Parámetros opcionales
    min_threshold = 50  # Valor por defecto - conservador
    if len(sys.argv) > 3 and sys.argv[3].isdigit():
        min_threshold = int(sys.argv[3])
        verbose_arg = 4
    else:
        verbose_arg = 3
    
    verbose = len(sys.argv) > verbose_arg and sys.argv[verbose_arg].lower() in ['true', '1', 'yes', 'v']
    
    print("🎨 Background Remover - Preservación de Elementos del Personaje")
    print("=" * 65)
    print("💡 CORRIGE transparencias parciales sin eliminar elementos del personaje")
    
    success = remove_background_preserve_elements(input_path, output_path, min_threshold, verbose)
    
    if success:
        print("\n🎉 Proceso completado exitosamente!")
        print("✅ Todos los elementos del personaje (globos, relojes, etc.) preservados")
        print("✨ Transparencias parciales corregidas a completamente opacas")
    else:
        print("\n💥 Error durante el procesamiento")
        sys.exit(1)


if __name__ == "__main__":
    main()
