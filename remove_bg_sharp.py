#!/usr/bin/env python3
"""
Advanced background removal script with anti-aliasing control
Usage: python remove_bg_sharp.py input_image output_image [options]
"""

import sys
import numpy as np
from rembg import remove, new_session
from PIL import Image, ImageFilter, ImageEnhance
import cv2

def apply_alpha_matting(image_array, mask_array, threshold=0.5, blur_radius=1):
    """
    Apply alpha matting to reduce soft edges and improve sharpness
    """
    # Convert mask to binary with threshold
    binary_mask = (mask_array > threshold * 255).astype(np.uint8) * 255
    
    # Apply slight blur to soften harsh edges if needed
    if blur_radius > 0:
        binary_mask = cv2.GaussianBlur(binary_mask, (blur_radius*2+1, blur_radius*2+1), 0)
    
    return binary_mask

def sharpen_edges(image, mask, sharpen_factor=1.5):
    """
    Sharpen the edges of the mask for cleaner cutout
    """
    # Convert PIL to numpy
    img_array = np.array(image)
    mask_array = np.array(mask)
    
    # Apply edge detection to find contours
    edges = cv2.Canny(mask_array, 50, 150)
    
    # Dilate edges slightly
    kernel = np.ones((3,3), np.uint8)
    edges_dilated = cv2.dilate(edges, kernel, iterations=1)
    
    # Sharpen the mask around edges
    sharpened_mask = mask_array.copy()
    edge_pixels = edges_dilated > 0
    
    # Make edge pixels more decisive (closer to 0 or 255)
    edge_values = sharpened_mask[edge_pixels]
    edge_values = np.where(edge_values > 127, 
                          np.minimum(255, edge_values * sharpen_factor),
                          np.maximum(0, edge_values / sharpen_factor))
    sharpened_mask[edge_pixels] = edge_values
    
    return Image.fromarray(sharpened_mask)

def remove_background_sharp(input_path, output_path, model_name='u2net', 
                           alpha_threshold=0.8, edge_enhance=True, 
                           sharpen_factor=1.5, blur_reduction=True):
    """
    Remove background with enhanced edge control
    
    Args:
        input_path (str): Path to input image
        output_path (str): Path to save output image
        model_name (str): Model to use
        alpha_threshold (float): Threshold for alpha channel (0.0-1.0)
        edge_enhance (bool): Apply edge enhancement
        sharpen_factor (float): Factor for edge sharpening
        blur_reduction (bool): Reduce blur in transparency
    """
    try:
        print(f"🔄 Processing {input_path}...")
        print(f"   Model: {model_name}")
        print(f"   Alpha threshold: {alpha_threshold}")
        print(f"   Edge enhancement: {edge_enhance}")
        
        # Create session with specific model
        if model_name != 'u2net':
            session = new_session(model_name)
            with open(input_path, 'rb') as input_file:
                input_data = input_file.read()
            output_data = remove(input_data, session=session)
        else:
            with open(input_path, 'rb') as input_file:
                input_data = input_file.read()
            output_data = remove(input_data)
        
        # Load the result as PIL Image
        import io
        result_image = Image.open(io.BytesIO(output_data)).convert("RGBA")
        
        if blur_reduction or edge_enhance:
            print("🔧 Applying post-processing...")
            
            # Get the alpha channel
            alpha = result_image.split()[-1]
            
            if blur_reduction:
                # Apply threshold to reduce soft transparency
                alpha_array = np.array(alpha)
                alpha_binary = apply_alpha_matting(alpha_array, alpha_array, 
                                                 threshold=alpha_threshold, 
                                                 blur_radius=0)
                alpha = Image.fromarray(alpha_binary)
            
            if edge_enhance:
                # Sharpen edges
                alpha = sharpen_edges(result_image, alpha, sharpen_factor)
            
            # Combine with original RGB channels
            rgb = result_image.convert("RGB")
            result_image = Image.merge("RGBA", (*rgb.split(), alpha))
        
        # Save the result
        result_image.save(output_path, format='PNG')
        
        print(f"✓ Background removed successfully!")
        print(f"Input: {input_path}")
        print(f"Output: {output_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def create_clean_cutout(input_path, output_path, model_name='isnet-general-use'):
    """
    Create a very clean cutout with minimal soft edges
    """
    print("🎯 Creating clean cutout with minimal soft edges...")
    return remove_background_sharp(
        input_path, output_path, model_name, 
        alpha_threshold=0.9, 
        edge_enhance=True, 
        sharpen_factor=2.0, 
        blur_reduction=True
    )

def create_soft_cutout(input_path, output_path, model_name='u2net'):
    """
    Create a softer cutout with some anti-aliasing preserved
    """
    print("🌊 Creating soft cutout with preserved anti-aliasing...")
    return remove_background_sharp(
        input_path, output_path, model_name, 
        alpha_threshold=0.5, 
        edge_enhance=False, 
        sharpen_factor=1.0, 
        blur_reduction=False
    )

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python remove_bg_sharp.py input_image output_image [mode] [model]")
        print("\nModes:")
        print("  clean  - Clean cutout with minimal soft edges (default)")
        print("  soft   - Soft cutout with preserved anti-aliasing")
        print("  custom - Custom settings")
        print("\nModels:")
        print("  u2net (default) - Good general purpose")
        print("  isnet-general-use - Better for clean edges")
        print("  u2netp - Lighter model")
        print("  silueta - Good for people")
        print("\nExamples:")
        print("  python remove_bg_sharp.py input.png output.png")
        print("  python remove_bg_sharp.py input.png output.png clean isnet-general-use")
        print("  python remove_bg_sharp.py input.png output.png soft u2net")
        sys.exit(1)
    
    input_image = sys.argv[1]
    output_image = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else 'clean'
    model = sys.argv[4] if len(sys.argv) > 4 else ('isnet-general-use' if mode == 'clean' else 'u2net')
    
    if mode == 'clean':
        create_clean_cutout(input_image, output_image, model)
    elif mode == 'soft':
        create_soft_cutout(input_image, output_image, model)
    elif mode == 'custom':
        # Custom settings - you can modify these
        remove_background_sharp(
            input_image, output_image, model,
            alpha_threshold=0.75,  # Adjust this (0.0-1.0)
            edge_enhance=True,     # True/False
            sharpen_factor=1.8,    # Adjust this (1.0-3.0)
            blur_reduction=True    # True/False
        )
    else:
        print(f"❌ Unknown mode: {mode}")
        print("Available modes: clean, soft, custom")
