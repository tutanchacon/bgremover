#!/usr/bin/env python3
"""
Corte completo de modelo humano - Detecta y extrae TODA la silueta del modelo
Especializado para cortar el modelo humano completo, no solo eliminar fondo blanco
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

def detect_full_human_silhouette(image):
    """Detecta la silueta humana completa usando múltiples técnicas"""
    img_array = np.array(image)
    
    # 1. Detección por contraste (para fondos uniformes)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # 2. Detectar bordes del modelo
    edges = cv2.Canny(gray, 30, 100)
    
    # 3. Dilatar bordes para conectar partes del cuerpo
    kernel = np.ones((5,5), np.uint8)
    edges_dilated = cv2.dilate(edges, kernel, iterations=2)
    
    # 4. Encontrar contornos
    contours, _ = cv2.findContours(edges_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 5. Encontrar el contorno más grande (debería ser el modelo)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Crear máscara del contorno
        mask = np.zeros(gray.shape, np.uint8)
        cv2.fillPoly(mask, [largest_contour], 255)
        
        # Suavizar la máscara
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        return mask
    
    return None

def enhance_human_mask_complete(mask_ai, mask_contour, original_shape):
    """Combina máscaras de AI y detección de contornos para captura completa"""
    
    # Redimensionar máscaras si es necesario
    if mask_ai.shape != original_shape[:2]:
        mask_ai = cv2.resize(mask_ai, (original_shape[1], original_shape[0]))
    
    if mask_contour is not None and mask_contour.shape != original_shape[:2]:
        mask_contour = cv2.resize(mask_contour, (original_shape[1], original_shape[0]))
    
    # Combinar máscaras usando OR lógico para capturar TODO
    if mask_contour is not None:
        # Tomar el máximo de ambas máscaras para incluir todo
        combined_mask = np.maximum(mask_ai, mask_contour)
    else:
        combined_mask = mask_ai
    
    # Morfología para incluir partes que pueden haberse perdido
    kernel_large = np.ones((15, 15), np.uint8)
    
    # Cerrar gaps en la silueta
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel_large)
    
    # Dilatar ligeramente para asegurar que capturamos todo el modelo
    kernel_dilate = np.ones((7, 7), np.uint8)
    combined_mask = cv2.dilate(combined_mask, kernel_dilate, iterations=1)
    
    # Llenar huecos internos
    contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        # Tomar el contorno más grande y llenarlo completamente
        largest_contour = max(contours, key=cv2.contourArea)
        combined_mask = np.zeros_like(combined_mask)
        cv2.fillPoly(combined_mask, [largest_contour], 255)
    
    # Suavizar bordes finales
    combined_mask = cv2.GaussianBlur(combined_mask, (3, 3), 0)
    
    return combined_mask

def cut_complete_human_model(input_path, output_path, aggressiveness='complete'):
    """
    Corta el modelo humano COMPLETO de la imagen
    
    Args:
        input_path: Ruta de imagen de entrada
        output_path: Ruta de imagen de salida  
        aggressiveness: 'conservative', 'balanced', 'complete', 'aggressive'
    """
    try:
        print("🎯 Iniciando corte COMPLETO del modelo humano...")
        
        # Cargar imagen original
        with Image.open(input_path) as img:
            original = img.convert('RGBA')
            original_rgb = img.convert('RGB')
            print(f"📐 Procesando imagen: {original.size}")
        
        # 1. Usar AI especializada en humanos
        print("🤖 Detectando silueta con AI especializada...")
        session = new_session('u2net_human_seg')
        ai_result = remove(original_rgb, session=session)
        
        # Extraer máscara de AI
        ai_mask = np.array(ai_result)[:,:,3]
        
        # 2. Detectar contornos del modelo
        print("🔍 Detectando contornos del modelo...")
        contour_mask = detect_full_human_silhouette(original_rgb)
        
        # 3. Combinar técnicas para captura completa
        print("🎯 Combinando técnicas para captura completa...")
        final_mask = enhance_human_mask_complete(ai_mask, contour_mask, np.array(original).shape)
        
        # 4. Ajustar agresividad según parámetro
        if aggressiveness == 'aggressive':
            # Dilatar más para capturar absolutamente todo
            kernel = np.ones((15, 15), np.uint8)
            final_mask = cv2.dilate(final_mask, kernel, iterations=2)
        elif aggressiveness == 'complete':
            # Nivel balanceado para captura completa
            kernel = np.ones((9, 9), np.uint8)
            final_mask = cv2.dilate(final_mask, kernel, iterations=1)
        elif aggressiveness == 'conservative':
            # Solo usar resultado de AI
            final_mask = ai_mask
        
        # 5. Limpiar bordes
        print("✨ Limpiando y refinando bordes...")
        
        # Aplicar threshold para bordes definidos
        _, final_mask = cv2.threshold(final_mask, 127, 255, cv2.THRESH_BINARY)
        
        # Suavizar bordes levemente
        final_mask = cv2.medianBlur(final_mask, 3)
        
        # 6. Aplicar máscara a imagen original
        original_array = np.array(original)
        
        # Aplicar la máscara al canal alpha
        original_array[:,:,3] = final_mask
        
        # Crear imagen final
        result_image = Image.fromarray(original_array, 'RGBA')
        
        # Guardar resultado
        result_image.save(output_path, 'PNG')
        
        print(f"✅ ¡Modelo humano cortado completamente!")
        print(f"💾 Guardado en: {output_path}")
        print(f"🎯 Nivel de captura: {aggressiveness}")
        
        # Mostrar estadísticas de la máscara
        pixels_modelo = np.sum(final_mask > 127)
        pixels_total = final_mask.shape[0] * final_mask.shape[1]
        porcentaje = (pixels_modelo / pixels_total) * 100
        print(f"📊 Modelo capturado: {porcentaje:.1f}% de la imagen")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el corte: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("🎯 Uso: python cut_complete_model.py <imagen_entrada> <imagen_salida> [agresividad]")
        print("📝 Niveles de agresividad:")
        print("   conservative - Solo AI (más conservador)")
        print("   balanced     - AI + contornos (balanceado)")  
        print("   complete     - Captura completa (recomendado)")
        print("   aggressive   - Máxima captura (más agresivo)")
        print("💡 Ejemplo: python cut_complete_model.py modelo.jpg modelo_cortado.png complete")
        print("🎯 Especializado para cortar TODO el modelo humano")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    aggressiveness = sys.argv[3] if len(sys.argv) > 3 else 'complete'
    
    if not os.path.exists(input_path):
        print(f"❌ Error: No se encuentra el archivo {input_path}")
        sys.exit(1)
    
    success = cut_complete_human_model(input_path, output_path, aggressiveness)
    
    if success:
        print("\n🎉 ¡Corte completo del modelo exitoso!")
        print("💡 Si necesitas capturar más partes, prueba con 'aggressive'")
        print("💡 Si captura demasiado, prueba con 'conservative'")
    else:
        print("\n💥 El corte falló")
        sys.exit(1)

if __name__ == "__main__":
    main()
