"""
Core background removal functionality
"""
import cv2
import numpy as np
from rembg import remove, new_session
from PIL import Image
import os
import io
from scipy import ndimage
from typing import Optional, Tuple, Union
import logging

logger = logging.getLogger(__name__)


class BackgroundRemover:
    """
    Professional background remover with element preservation.
    
    This class provides advanced background removal capabilities that preserve
    character elements while removing only the true background.
    
    Features:
    - Element preservation (accessories, props, etc.)
    - Partial transparency correction
    - Professional edge smoothing
    - Multiple output formats
    
    Example:
        >>> remover = BackgroundRemover()
        >>> success = remover.remove_background('input.jpg', 'output.png')
        >>> if success:
        ...     print("Background removed successfully!")
    """
    
    def __init__(self, model_name: str = 'isnet-general-use'):
        """
        Initialize the background remover.
        
        Args:
            model_name: The rembg model to use. Default is 'isnet-general-use'
        """
        self.model_name = model_name
        self.session = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the rembg model session."""
        try:
            self.session = new_session(self.model_name)
            logger.info(f"Initialized {self.model_name} model successfully")
        except Exception as e:
            logger.error(f"Failed to initialize model {self.model_name}: {e}")
            raise
    
    def remove_background(
        self, 
        input_path: str, 
        output_path: str, 
        min_alpha_threshold: int = 50,
        preserve_elements: bool = True,
        smooth_edges: bool = True,
        verbose: bool = False
    ) -> bool:
        """
        Remove background from an image while preserving character elements.
        
        Args:
            input_path: Path to input image
            output_path: Path to save output image
            min_alpha_threshold: Minimum alpha value to preserve (0-255)
            preserve_elements: Whether to preserve character elements
            smooth_edges: Whether to apply edge smoothing
            verbose: Whether to print detailed progress information
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if verbose:
                print(f"📸 Processing: {input_path}")
                print(f"🎯 Alpha threshold: {min_alpha_threshold}")
            
            # Validate input
            if not os.path.exists(input_path):
                logger.error(f"Input file not found: {input_path}")
                return False
            
            # Load and process image
            with open(input_path, 'rb') as f:
                input_data = f.read()
            
            if verbose:
                print("🤖 Applying AI segmentation...")
            
            output_data = remove(input_data, session=self.session)
            
            # Convert to PIL and numpy arrays
            img_pil = Image.open(input_path).convert('RGBA')
            result_pil = Image.open(io.BytesIO(output_data))
            
            img_array = np.array(img_pil)
            result_array = np.array(result_pil)
            
            # Apply processing pipeline
            if preserve_elements:
                result_array = self._preserve_elements_pipeline(
                    result_array, min_alpha_threshold, verbose
                )
            
            if smooth_edges:
                result_array = self._smooth_edges_conservative(result_array)
            
            # Save result
            result_final = Image.fromarray(result_array)
            result_final.save(output_path, format='PNG')
            
            if verbose:
                print(f"✅ Saved to: {output_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            if verbose:
                print(f"❌ Error: {e}")
            return False
    
    def _preserve_elements_pipeline(
        self, 
        img_array: np.ndarray, 
        min_threshold: int, 
        verbose: bool = False
    ) -> np.ndarray:
        """Apply element preservation pipeline."""
        result = img_array.copy()
        
        if verbose:
            print("🔍 Analyzing transparency distribution...")
        result = self._analyze_alpha_distribution(result, verbose)
        
        if verbose:
            print(f"✨ Fixing partial transparencies (threshold: {min_threshold})...")
        result = self._fix_partial_transparencies(result, min_threshold, verbose)
        
        if verbose:
            print("🔗 Connecting character elements...")
        result = self._connect_character_elements(result, verbose)
        
        if verbose:
            print("🧹 Cleaning background whites...")
        result = self._remove_background_whites_only(result)
        
        return result
    
    def _analyze_alpha_distribution(self, img_array: np.ndarray, verbose: bool = False) -> np.ndarray:
        """Analyze alpha channel distribution."""
        alpha = img_array[:,:,3]
        total_pixels = alpha.shape[0] * alpha.shape[1]
        
        if verbose:
            transparent = np.sum(alpha == 0)
            very_low = np.sum((alpha > 0) & (alpha <= 50))
            low = np.sum((alpha > 50) & (alpha <= 100))
            medium = np.sum((alpha > 100) & (alpha <= 180))
            high = np.sum((alpha > 180) & (alpha < 255))
            solid = np.sum(alpha == 255)
            
            print(f"   📊 Alpha distribution:")
            print(f"   - Transparent (0): {(transparent/total_pixels)*100:.1f}%")
            print(f"   - Very low (1-50): {(very_low/total_pixels)*100:.1f}%")
            print(f"   - Low (51-100): {(low/total_pixels)*100:.1f}%")
            print(f"   - Medium (101-180): {(medium/total_pixels)*100:.1f}%")
            print(f"   - High (181-254): {(high/total_pixels)*100:.1f}%")
            print(f"   - Solid (255): {(solid/total_pixels)*100:.1f}%")
        
        return img_array
    
    def _fix_partial_transparencies(
        self, 
        img_array: np.ndarray, 
        min_threshold: int, 
        verbose: bool = False
    ) -> np.ndarray:
        """Fix partial transparencies by converting to fully opaque."""
        result = img_array.copy()
        alpha = result[:,:,3]
        
        # Remove noise (very low alpha values)
        noise_mask = (alpha > 0) & (alpha < min_threshold)
        result[noise_mask, 3] = 0
        
        # Convert partial transparencies to fully opaque
        character_elements_mask = (alpha >= min_threshold) & (alpha < 255)
        result[character_elements_mask, 3] = 255
        
        if verbose:
            noise_removed = np.sum(noise_mask)
            elements_fixed = np.sum(character_elements_mask)
            print(f"   ❌ Noise removed: {noise_removed:,} pixels")
            print(f"   ✅ Elements fixed: {elements_fixed:,} pixels")
        
        return result
    
    def _connect_character_elements(self, img_array: np.ndarray, verbose: bool = False) -> np.ndarray:
        """Connect disconnected character elements."""
        result = img_array.copy()
        alpha = result[:,:,3]
        
        # Apply morphological closing to connect nearby elements
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        alpha_closed = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, kernel)
        
        # Only apply where there were originally some alpha values
        mask = alpha > 0
        result[mask, 3] = alpha_closed[mask]
        
        return result
    
    def _remove_background_whites_only(self, img_array: np.ndarray) -> np.ndarray:
        """Remove only white background pixels."""
        result = img_array.copy()
        
        # Create mask for white/near-white pixels
        rgb = result[:,:,:3]
        white_mask = np.all(rgb > 240, axis=2)
        
        # Only remove whites that have low alpha (likely background)
        background_whites = white_mask & (result[:,:,3] < 200)
        result[background_whites, 3] = 0
        
        return result
    
    def _smooth_edges_conservative(self, img_array: np.ndarray) -> np.ndarray:
        """Apply conservative edge smoothing."""
        result = img_array.copy()
        alpha = result[:,:,3].astype(np.float32)
        
        # Apply light Gaussian blur to alpha channel
        alpha_smooth = cv2.GaussianBlur(alpha, (3, 3), 0.5)
        
        # Only apply smoothing to edge pixels
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.morphologyEx((alpha > 0).astype(np.uint8), cv2.MORPH_GRADIENT, kernel)
        
        alpha[edges > 0] = alpha_smooth[edges > 0]
        result[:,:,3] = np.clip(alpha, 0, 255).astype(np.uint8)
        
        return result
    
    def get_stats(self, image_path: str) -> dict:
        """
        Get statistics about an image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            dict: Image statistics
        """
        try:
            with Image.open(image_path) as img:
                if img.mode == 'RGBA':
                    alpha = np.array(img)[:,:,3]
                    total_pixels = alpha.shape[0] * alpha.shape[1]
                    visible_pixels = np.sum(alpha > 0)
                    
                    return {
                        'width': img.width,
                        'height': img.height,
                        'total_pixels': total_pixels,
                        'visible_pixels': visible_pixels,
                        'transparency_percentage': (visible_pixels / total_pixels) * 100,
                        'has_transparency': True
                    }
                else:
                    return {
                        'width': img.width,
                        'height': img.height,
                        'total_pixels': img.width * img.height,
                        'visible_pixels': img.width * img.height,
                        'transparency_percentage': 100.0,
                        'has_transparency': False
                    }
        except Exception as e:
            logger.error(f"Error getting image stats: {e}")
            return {}
