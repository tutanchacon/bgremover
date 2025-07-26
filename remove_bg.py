#!/usr/bin/env python3
"""
Simple background removal script using rembg library
Usage: python remove_bg.py input_image output_image [model]
"""

import sys
from rembg import remove
from PIL import Image

def remove_background(input_path, output_path, model_name='u2net'):
    """
    Remove background from an image
    
    Args:
        input_path (str): Path to input image
        output_path (str): Path to save output image
        model_name (str): Model to use (u2net, u2netp, silueta, isnet-general-use, etc.)
    """
    try:
        # Open input image
        with open(input_path, 'rb') as input_file:
            input_data = input_file.read()
        
        # Remove background
        output_data = remove(input_data)
        
        # Save output image
        with open(output_path, 'wb') as output_file:
            output_file.write(output_data)
        
        print(f"✓ Background removed successfully!")
        print(f"Input: {input_path}")
        print(f"Output: {output_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python remove_bg.py input_image output_image [model]")
        print("Example: python remove_bg.py input.png output.png")
        print("Available models: u2net, u2netp, silueta, isnet-general-use")
        sys.exit(1)
    
    input_image = sys.argv[1]
    output_image = sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else 'u2net'
    
    remove_background(input_image, output_image, model)
