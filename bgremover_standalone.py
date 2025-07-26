"""
Standalone BGRemover Library - Copy this file to your project
============================================================

Uso:
1. Copia este archivo a tu proyecto: bgremover_lib.py
2. Instala dependencias: pip install rembg opencv-python pillow numpy scipy
3. Úsalo en tu código:

    from bgremover_lib import BackgroundRemoverStandalone
    
    remover = BackgroundRemoverStandalone()
    success = remover.process('input.jpg', 'output.png')
"""

import cv2
import numpy as np
from rembg import remove, new_session
from PIL import Image
import os
import io
from typing import Optional


class BackgroundRemoverStandalone:
    """
    Standalone background remover - no external dependencies on your package.
    
    Features:
    - Element preservation
    - Professional quality
    - Easy integration
    - Single file solution
    """
    
    def __init__(self, model_name: str = 'isnet-general-use'):
        """Initialize the background remover."""
        self.model_name = model_name
        self.session = new_session(model_name)
    
    def process(
        self, 
        input_path: str, 
        output_path: str, 
        threshold: int = 20,
        verbose: bool = False
    ) -> bool:
        """
        Remove background from image.
        
        Args:
            input_path: Input image path
            output_path: Output image path  
            threshold: Alpha threshold (0-255)
            verbose: Show progress info
            
        Returns:
            bool: Success status
        """
        try:
            if verbose:
                print(f"🎯 Processing: {input_path}")
            
            # Validate input
            if not os.path.exists(input_path):
                print(f"❌ File not found: {input_path}")
                return False
            
            # Process with rembg
            with open(input_path, 'rb') as f:
                input_data = f.read()
            
            output_data = remove(input_data, session=self.session)
            
            # Convert to PIL and numpy
            result_pil = Image.open(io.BytesIO(output_data))
            result_array = np.array(result_pil)
            
            # Apply processing pipeline
            result_array = self._fix_transparencies(result_array, threshold)
            result_array = self._smooth_edges(result_array)
            
            # Save result
            result_final = Image.fromarray(result_array)
            result_final.save(output_path, format='PNG')
            
            if verbose:
                print(f"✅ Saved: {output_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def _fix_transparencies(self, img_array: np.ndarray, threshold: int) -> np.ndarray:
        """Fix partial transparencies."""
        result = img_array.copy()
        alpha = result[:,:,3]
        
        # Remove noise
        noise_mask = (alpha > 0) & (alpha < threshold)
        result[noise_mask, 3] = 0
        
        # Fix partial transparencies
        partial_mask = (alpha >= threshold) & (alpha < 255)
        result[partial_mask, 3] = 255
        
        return result
    
    def _smooth_edges(self, img_array: np.ndarray) -> np.ndarray:
        """Apply edge smoothing."""
        result = img_array.copy()
        alpha = result[:,:,3].astype(np.float32)
        
        # Light smoothing
        alpha_smooth = cv2.GaussianBlur(alpha, (3, 3), 0.5)
        
        # Apply only to edges
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.morphologyEx((alpha > 0).astype(np.uint8), cv2.MORPH_GRADIENT, kernel)
        
        alpha[edges > 0] = alpha_smooth[edges > 0]
        result[:,:,3] = np.clip(alpha, 0, 255).astype(np.uint8)
        
        return result


# Función de conveniencia
def remove_background_quick(input_path: str, output_path: str, threshold: int = 20) -> bool:
    """
    Quick background removal function.
    
    Args:
        input_path: Input image path
        output_path: Output image path
        threshold: Alpha threshold (default: 20)
        
    Returns:
        bool: Success status
    """
    remover = BackgroundRemoverStandalone()
    return remover.process(input_path, output_path, threshold, verbose=True)


# Ejemplo de uso
if __name__ == "__main__":
    # Uso básico
    success = remove_background_quick("input.jpg", "output.png")
    
    # Uso avanzado
    remover = BackgroundRemoverStandalone()
    success = remover.process("input.jpg", "output.png", threshold=20, verbose=True)
