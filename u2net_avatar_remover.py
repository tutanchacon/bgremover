#!/usr/bin/env python3
"""
U²-Net Enhanced Background Removal for Avatars/Models
Optimized to preserve fine details and avoid removing parts of the subject
"""

import sys
import numpy as np
from rembg import remove, new_session
from PIL import Image, ImageFilter, ImageEnhance
import cv2
import io

def enhance_avatar_mask(mask_array, preserve_details=True, smooth_edges=False):
    """
    Enhance mask specifically for avatars/models to preserve details
    
    Args:
        mask_array: numpy array of the alpha mask
        preserve_details: Keep fine details like hair, accessories, etc.
        smooth_edges: Apply slight smoothing to edges
    """
    enhanced_mask = mask_array.copy()
    
    if preserve_details:
        # Use morphological operations to preserve fine details
        kernel_small = np.ones((3,3), np.uint8)
        kernel_medium = np.ones((5,5), np.uint8)
        
        # Close small gaps (connect broken parts)
        enhanced_mask = cv2.morphologyEx(enhanced_mask, cv2.MORPH_CLOSE, kernel_small)
        
        # Fill holes in the mask
        enhanced_mask = cv2.morphologyEx(enhanced_mask, cv2.MORPH_CLOSE, kernel_medium)
        
        # Remove small noise but preserve main subject
        enhanced_mask = cv2.medianBlur(enhanced_mask, 3)
    
    if smooth_edges:
        # Very light gaussian blur to smooth edges without losing details
        enhanced_mask = cv2.GaussianBlur(enhanced_mask, (3,3), 0.5)
    
    return enhanced_mask

def apply_smart_threshold(mask_array, threshold_method='adaptive'):
    """
    Apply intelligent thresholding to preserve subject details
    
    Args:
        mask_array: numpy array of the alpha mask
        threshold_method: 'adaptive', 'otsu', or 'conservative'
    """
    if threshold_method == 'adaptive':
        # Adaptive threshold preserves local details
        binary_mask = cv2.adaptiveThreshold(
            mask_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        return binary_mask
    
    elif threshold_method == 'otsu':
        # Otsu's method for automatic threshold
        _, binary_mask = cv2.threshold(mask_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary_mask
    
    elif threshold_method == 'conservative':
        # Conservative threshold to avoid removing subject parts
        conservative_threshold = np.percentile(mask_array[mask_array > 0], 25)  # Use 25th percentile
        binary_mask = np.where(mask_array > conservative_threshold, 255, 0).astype(np.uint8)
        return binary_mask
    
    return mask_array

def remove_background_u2net_avatar(input_path, output_path, 
                                  model_type='u2net', 
                                  preserve_details=True,
                                  detail_enhancement=True,
                                  edge_refinement=True,
                                  mask_threshold='adaptive'):
    """
    Enhanced U²-Net background removal optimized for avatars/models
    
    Args:
        input_path (str): Path to input image
        output_path (str): Path to save output image
        model_type (str): 'u2net', 'u2net_human_seg', 'u2netp', 'silueta'
        preserve_details (bool): Preserve fine details like hair, accessories
        detail_enhancement (bool): Enhance mask details
        edge_refinement (bool): Refine edges
        mask_threshold (str): Threshold method for mask processing
    """
    
    print(f"🎯 U²-Net Avatar Background Removal")
    print(f"📁 Input: {input_path}")
    print(f"🤖 Model: {model_type}")
    print(f"🔍 Preserve details: {preserve_details}")
    print(f"⚡ Processing...")
    
    try:
        # Read input image
        with open(input_path, 'rb') as input_file:
            input_data = input_file.read()
        
        # Create session with specified model
        if model_type == 'u2net':
            # Standard U²-Net - best overall performance
            output_data = remove(input_data)
            print("✅ Using U²-Net standard model")
        elif model_type == 'u2net_human_seg':
            # Optimized for human segmentation
            session = new_session('u2net_human_seg')
            output_data = remove(input_data, session=session)
            print("✅ Using U²-Net human segmentation model")
        elif model_type == 'silueta':
            # Good for people/avatars
            session = new_session('silueta')
            output_data = remove(input_data, session=session)
            print("✅ Using Silueta model (optimized for people)")
        else:
            # Fallback to u2net
            output_data = remove(input_data)
            print("✅ Using U²-Net fallback")
        
        # Convert to PIL Image
        result_image = Image.open(io.BytesIO(output_data)).convert("RGBA")
        original_image = Image.open(input_path).convert("RGB")
        
        if preserve_details or detail_enhancement or edge_refinement:
            print("🔧 Applying avatar-specific enhancements...")
            
            # Extract alpha channel
            r, g, b, alpha = result_image.split()
            alpha_array = np.array(alpha)
            
            # Apply smart thresholding to preserve details
            if mask_threshold != 'none':
                alpha_array = apply_smart_threshold(alpha_array, mask_threshold)
                print(f"🎨 Applied {mask_threshold} thresholding")
            
            # Enhance mask for avatar preservation
            if preserve_details:
                alpha_array = enhance_avatar_mask(alpha_array, 
                                                preserve_details=True, 
                                                smooth_edges=edge_refinement)
                print("🎭 Enhanced mask for avatar details")
            
            # Additional detail enhancement
            if detail_enhancement:
                # Use bilateral filter to preserve edges while smoothing
                alpha_array = cv2.bilateralFilter(alpha_array, 9, 75, 75)
                print("✨ Applied detail enhancement")
            
            # Convert back to PIL
            enhanced_alpha = Image.fromarray(alpha_array)
            
            # Recombine channels
            result_image = Image.merge("RGBA", (r, g, b, enhanced_alpha))
        
        # Save result
        result_image.save(output_path, 'PNG', optimize=True)
        
        print(f"✅ Success! Avatar background removed")
        print(f"💾 Saved to: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_avatar_presets():
    """Create preset configurations for different avatar types"""
    
    presets = {
        'portrait': {
            'model_type': 'u2net_human_seg',
            'preserve_details': True,
            'detail_enhancement': True,
            'edge_refinement': True,
            'mask_threshold': 'adaptive',
            'description': 'Optimized for portrait avatars and headshots'
        },
        'full_body': {
            'model_type': 'u2net',
            'preserve_details': True,
            'detail_enhancement': True,
            'edge_refinement': False,
            'mask_threshold': 'conservative',
            'description': 'Best for full body avatars and models'
        },
        'detailed': {
            'model_type': 'silueta',
            'preserve_details': True,
            'detail_enhancement': True,
            'edge_refinement': True,
            'mask_threshold': 'adaptive',
            'description': 'Maximum detail preservation for complex avatars'
        },
        'clean': {
            'model_type': 'u2net',
            'preserve_details': False,
            'detail_enhancement': False,
            'edge_refinement': True,
            'mask_threshold': 'otsu',
            'description': 'Clean cutout with smooth edges'
        }
    }
    
    return presets

def process_avatar_with_preset(input_path, output_path, preset_name='portrait'):
    """
    Process avatar using predefined preset
    
    Args:
        input_path (str): Path to input image
        output_path (str): Path to save output image
        preset_name (str): Preset to use ('portrait', 'full_body', 'detailed', 'clean')
    """
    presets = create_avatar_presets()
    
    if preset_name not in presets:
        print(f"❌ Unknown preset: {preset_name}")
        print(f"Available presets: {', '.join(presets.keys())}")
        return False
    
    preset = presets[preset_name]
    print(f"🎨 Using preset: {preset_name} - {preset['description']}")
    
    return remove_background_u2net_avatar(
        input_path, output_path,
        model_type=preset['model_type'],
        preserve_details=preset['preserve_details'],
        detail_enhancement=preset['detail_enhancement'],
        edge_refinement=preset['edge_refinement'],
        mask_threshold=preset['mask_threshold']
    )

def main():
    print("🎭 U²-Net Avatar Background Removal Tool")
    print("=" * 50)
    
    if len(sys.argv) < 3:
        print("Usage: python u2net_avatar_remover.py input output [preset]")
        print("\n🎨 Available presets:")
        presets = create_avatar_presets()
        for name, config in presets.items():
            print(f"  {name:10} - {config['description']}")
        print("\n💡 Examples:")
        print("  python u2net_avatar_remover.py avatar.jpg result.png")
        print("  python u2net_avatar_remover.py avatar.jpg result.png portrait")
        print("  python u2net_avatar_remover.py avatar.jpg result.png detailed")
        return
    
    input_image = sys.argv[1]
    output_image = sys.argv[2]
    preset = sys.argv[3] if len(sys.argv) > 3 else 'portrait'
    
    success = process_avatar_with_preset(input_image, output_image, preset)
    
    if success:
        print("\n🎉 Processing completed successfully!")
        print("💡 Tip: Try different presets if the result needs adjustment")
    else:
        print("\n❌ Processing failed")

if __name__ == "__main__":
    main()
