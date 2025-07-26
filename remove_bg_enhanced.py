#!/usr/bin/env python3
"""
Enhanced background removal with sharp edges
Usage: python remove_bg_enhanced.py input_image output_image [threshold]
"""

import sys
import numpy as np
from rembg import remove, new_session
from PIL import Image, ImageFilter
import io

def enhance_alpha_channel(alpha_channel, threshold=200, sharpen=True):
    """
    Enhance alpha channel to reduce blur and create sharper edges
    
    Args:
        alpha_channel: PIL Image alpha channel
        threshold: Value above which pixels become fully opaque (0-255)
        sharpen: Whether to apply sharpening filter
    """
    # Convert to numpy array for processing
    alpha_array = np.array(alpha_channel)
    
    # Apply threshold to create more decisive transparency
    # Values above threshold become fully opaque, below become more transparent
    alpha_enhanced = np.where(alpha_array > threshold, 255, 
                             np.where(alpha_array < (threshold//3), 0, alpha_array))
    
    # Convert back to PIL Image
    alpha_enhanced_img = Image.fromarray(alpha_enhanced.astype(np.uint8))
    
    # Apply sharpening filter to reduce soft edges
    if sharpen:
        # Create a custom sharpening kernel
        sharpen_filter = ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3)
        alpha_enhanced_img = alpha_enhanced_img.filter(sharpen_filter)
    
    return alpha_enhanced_img

def remove_background_enhanced(input_path, output_path, model_name='isnet-general-use', 
                              alpha_threshold=200, apply_sharpening=True):
    """
    Remove background with enhanced edge sharpness
    
    Args:
        input_path (str): Path to input image
        output_path (str): Path to save output image  
        model_name (str): Model to use for background removal
        alpha_threshold (int): Threshold for alpha enhancement (0-255)
        apply_sharpening (bool): Whether to apply edge sharpening
    """
    try:
        print(f"🔄 Processing: {input_path}")
        print(f"   Model: {model_name}")
        print(f"   Alpha threshold: {alpha_threshold}")
        print(f"   Sharpening: {'Enabled' if apply_sharpening else 'Disabled'}")
        
        # Read input image
        with open(input_path, 'rb') as input_file:
            input_data = input_file.read()
        
        # Remove background using specified model
        if model_name == 'u2net':
            output_data = remove(input_data)
        else:
            session = new_session(model_name)
            output_data = remove(input_data, session=session)
        
        # Convert to PIL Image
        result_image = Image.open(io.BytesIO(output_data)).convert("RGBA")
        
        # Enhance alpha channel for sharper edges
        if alpha_threshold < 255 or apply_sharpening:
            print("🔧 Enhancing alpha channel for sharper edges...")
            
            # Split channels
            r, g, b, alpha = result_image.split()
            
            # Enhance the alpha channel
            enhanced_alpha = enhance_alpha_channel(alpha, alpha_threshold, apply_sharpening)
            
            # Recombine channels
            result_image = Image.merge("RGBA", (r, g, b, enhanced_alpha))
        
        # Save result
        result_image.save(output_path, format='PNG', optimize=True)
        
        print(f"✓ Success! Saved to: {output_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Enhanced Background Removal Tool")
        print("=" * 40)
        print("Usage: python remove_bg_enhanced.py input output [threshold] [model]")
        print("\nParameters:")
        print("  threshold: Alpha threshold 0-255 (default: 200)")
        print("             Lower = softer edges, Higher = sharper edges")
        print("  model: AI model to use (default: isnet-general-use)")
        print("\nAvailable models:")
        print("  • isnet-general-use - Best for sharp, clean edges")
        print("  • u2net - Good general purpose model") 
        print("  • u2netp - Lighter/faster model")
        print("  • silueta - Good for people/portraits")
        print("\nExamples:")
        print("  python remove_bg_enhanced.py photo.jpg result.png")
        print("  python remove_bg_enhanced.py photo.jpg sharp.png 220")
        print("  python remove_bg_enhanced.py photo.jpg soft.png 150 u2net")
        sys.exit(1)
    
    input_image = sys.argv[1]
    output_image = sys.argv[2]
    threshold = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    model = sys.argv[4] if len(sys.argv) > 4 else 'isnet-general-use'
    
    # Validate threshold
    if threshold < 0 or threshold > 255:
        print("❌ Error: Threshold must be between 0 and 255")
        sys.exit(1)
    
    remove_background_enhanced(input_image, output_image, model, threshold, True)
