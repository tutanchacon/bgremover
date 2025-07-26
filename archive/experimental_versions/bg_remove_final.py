#!/usr/bin/env python3
"""
Ultimate Background Removal Tool - Reduces blur and creates sharp edges
Usage: python bg_remove_final.py input output [mode]
"""

import sys
import numpy as np
from rembg import remove, new_session
from PIL import Image, ImageFilter, ImageOps
import io

def create_sharp_mask(alpha_channel, method='threshold'):
    """
    Create sharp mask with minimal soft edges
    
    Args:
        alpha_channel: PIL Image alpha channel
        method: 'threshold', 'binary', or 'enhanced'
    """
    alpha_array = np.array(alpha_channel)
    
    if method == 'binary':
        # Pure binary - either fully transparent or fully opaque
        binary_mask = np.where(alpha_array > 127, 255, 0)
        return Image.fromarray(binary_mask.astype(np.uint8))
    
    elif method == 'threshold':
        # Smart threshold - preserves some anti-aliasing but reduces blur
        threshold_high = 200
        threshold_low = 50
        
        sharp_mask = np.where(alpha_array > threshold_high, 255,
                             np.where(alpha_array < threshold_low, 0, 
                                    (alpha_array - threshold_low) * 255 // (threshold_high - threshold_low)))
        return Image.fromarray(sharp_mask.astype(np.uint8))
    
    elif method == 'enhanced':
        # Enhanced processing with edge detection
        from scipy import ndimage
        
        # Apply edge enhancement
        edges = ndimage.sobel(alpha_array)
        edge_strength = np.abs(edges)
        
        # Strengthen edges while preserving smooth areas
        enhanced = alpha_array.copy()
        edge_pixels = edge_strength > np.percentile(edge_strength, 70)
        enhanced[edge_pixels] = np.where(enhanced[edge_pixels] > 127, 255, 0)
        
        return Image.fromarray(enhanced.astype(np.uint8))
    
    return alpha_channel

def remove_bg_ultimate(input_path, output_path, mode='sharp'):
    """
    Ultimate background removal with customizable sharpness
    
    Modes:
        'sharp' - Maximum sharpness, minimal soft edges
        'clean' - Balanced sharpness with some anti-aliasing  
        'soft' - Preserve original soft edges
        'binary' - Pure binary mask (no anti-aliasing)
    """
    
    mode_configs = {
        'binary': {'model': 'isnet-general-use', 'mask_method': 'binary', 'description': 'Pure binary edges'},
        'sharp': {'model': 'isnet-general-use', 'mask_method': 'threshold', 'description': 'Sharp edges with minimal blur'},
        'clean': {'model': 'u2net', 'mask_method': 'enhanced', 'description': 'Clean balanced result'},
        'soft': {'model': 'u2net', 'mask_method': None, 'description': 'Preserve soft edges'}
    }
    
    if mode not in mode_configs:
        print(f"❌ Unknown mode: {mode}")
        print(f"Available modes: {', '.join(mode_configs.keys())}")
        return False
    
    config = mode_configs[mode]
    
    try:
        print(f"🎯 {config['description']}")
        print(f"📁 Input: {input_path}")
        print(f"🔧 Model: {config['model']}")
        print(f"⚡ Processing...")
        
        # Read input
        with open(input_path, 'rb') as f:
            input_data = f.read()
        
        # Remove background
        if config['model'] == 'u2net':
            output_data = remove(input_data)
        else:
            session = new_session(config['model'])
            output_data = remove(input_data, session=session)
        
        # Load result
        result = Image.open(io.BytesIO(output_data)).convert("RGBA")
        
        # Apply mask enhancement if specified
        if config['mask_method']:
            print(f"🔍 Applying {config['mask_method']} enhancement...")
            r, g, b, alpha = result.split()
            
            # Enhance alpha channel
            enhanced_alpha = create_sharp_mask(alpha, config['mask_method'])
            
            # Recombine
            result = Image.merge("RGBA", (r, g, b, enhanced_alpha))
        
        # Save result
        result.save(output_path, 'PNG', optimize=True)
        
        print(f"✅ Success! Saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🌟 Ultimate Background Removal Tool")
    print("=" * 50)
    
    if len(sys.argv) < 3:
        print("Usage: python bg_remove_final.py input output [mode]")
        print("\n🎨 Available modes:")
        print("  binary - Pure binary edges (no anti-aliasing)")
        print("  sharp  - Sharp edges with minimal blur (default)")
        print("  clean  - Balanced result with some anti-aliasing")
        print("  soft   - Preserve original soft edges")
        print("\n💡 Examples:")
        print("  python bg_remove_final.py photo.jpg result.png")
        print("  python bg_remove_final.py photo.jpg sharp.png sharp")
        print("  python bg_remove_final.py photo.jpg clean.png clean")
        return
    
    input_image = sys.argv[1]
    output_image = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else 'sharp'
    
    remove_bg_ultimate(input_image, output_image, mode)

if __name__ == "__main__":
    main()
