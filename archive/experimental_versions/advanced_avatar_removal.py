#!/usr/bin/env python3
"""
Advanced Avatar Detail Preservation Tool
Uses multiple techniques to ensure no parts of the avatar/model are lost
"""

import sys
import numpy as np
from rembg import remove, new_session
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import cv2
import io

def detect_subject_regions(image_array, mask_array):
    """
    Detect important subject regions that should never be removed
    """
    # Convert to grayscale for analysis
    gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    
    # Find edges in the original image
    edges = cv2.Canny(gray, 50, 150)
    
    # Find contours to identify subject regions
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Create a mask of important regions
    important_regions = np.zeros_like(gray)
    
    # Fill large contours (likely subject parts)
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 1000:  # Minimum area threshold
            cv2.fillPoly(important_regions, [contour], 255)
    
    return important_regions

def preserve_subject_details(original_mask, important_regions, preservation_strength=0.8):
    """
    Ensure important subject regions are preserved in the mask
    """
    preserved_mask = original_mask.copy()
    
    # Where we have important regions, strengthen the mask
    important_pixels = important_regions > 128
    preserved_mask[important_pixels] = np.maximum(
        preserved_mask[important_pixels],
        (important_regions[important_pixels] * preservation_strength).astype(np.uint8)
    )
    
    return preserved_mask

def multi_model_consensus(input_data, models=['u2net', 'u2net_human_seg', 'silueta']):
    """
    Use multiple models and combine their results for better accuracy
    """
    masks = []
    
    print(f"🔄 Running consensus with {len(models)} models...")
    
    for model_name in models:
        try:
            if model_name == 'u2net':
                output_data = remove(input_data)
            else:
                session = new_session(model_name)
                output_data = remove(input_data, session=session)
            
            # Extract mask
            result_image = Image.open(io.BytesIO(output_data)).convert("RGBA")
            _, _, _, alpha = result_image.split()
            masks.append(np.array(alpha))
            print(f"✅ {model_name} processed")
            
        except Exception as e:
            print(f"⚠️  {model_name} failed: {e}")
            continue
    
    if not masks:
        raise Exception("All models failed")
    
    # Combine masks using weighted average
    if len(masks) == 1:
        consensus_mask = masks[0]
    else:
        # Use intersection for conservative approach (keep only what all models agree on)
        consensus_mask = masks[0]
        for mask in masks[1:]:
            consensus_mask = np.minimum(consensus_mask, mask)
        
        # Also create a union version (keep what any model thinks is subject)
        union_mask = masks[0]
        for mask in masks[1:]:
            union_mask = np.maximum(union_mask, mask)
        
        # Blend intersection and union based on confidence
        consensus_mask = (consensus_mask * 0.7 + union_mask * 0.3).astype(np.uint8)
    
    print("✅ Model consensus completed")
    return consensus_mask

def advanced_avatar_removal(input_path, output_path, 
                           use_consensus=True,
                           preserve_strength=0.8,
                           detail_preservation=True,
                           safe_mode=True):
    """
    Advanced background removal that prevents losing avatar parts
    
    Args:
        input_path (str): Path to input image
        output_path (str): Path to save output image
        use_consensus (bool): Use multiple models for better accuracy
        preserve_strength (float): Strength of subject preservation (0-1)
        detail_preservation (bool): Apply detail preservation techniques
        safe_mode (bool): Use conservative settings to avoid losing subject parts
    """
    
    print(f"🎭 Advanced Avatar Detail Preservation")
    print(f"📁 Input: {input_path}")
    print(f"🛡️  Safe mode: {safe_mode}")
    print(f"🔍 Detail preservation: {detail_preservation}")
    print(f"🤝 Model consensus: {use_consensus}")
    print(f"⚡ Processing...")
    
    try:
        # Read input image
        with open(input_path, 'rb') as input_file:
            input_data = input_file.read()
        
        original_image = Image.open(input_path).convert("RGB")
        original_array = np.array(original_image)
        
        # Get mask using consensus or single model
        if use_consensus:
            if safe_mode:
                models = ['u2net_human_seg', 'silueta', 'u2net']  # Best models for humans
            else:
                models = ['u2net', 'u2net_human_seg']
            
            consensus_mask = multi_model_consensus(input_data, models)
        else:
            # Use best single model for humans
            session = new_session('u2net_human_seg')
            output_data = remove(input_data, session=session)
            result_image = Image.open(io.BytesIO(output_data)).convert("RGBA")
            _, _, _, alpha = result_image.split()
            consensus_mask = np.array(alpha)
            print("✅ Single model (u2net_human_seg) processed")
        
        # Detect important subject regions
        if detail_preservation:
            print("🔍 Detecting important subject regions...")
            important_regions = detect_subject_regions(original_array, consensus_mask)
            
            # Preserve subject details
            print("🛡️  Preserving subject details...")
            final_mask = preserve_subject_details(consensus_mask, important_regions, preserve_strength)
        else:
            final_mask = consensus_mask
        
        # Apply morphological operations to clean up the mask
        if safe_mode:
            # Conservative morphology - don't remove too much
            kernel = np.ones((3,3), np.uint8)
            final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel)
            final_mask = cv2.medianBlur(final_mask, 3)
            print("🧹 Applied conservative mask cleanup")
        
        # Apply slight smoothing to edges while preserving details
        if detail_preservation:
            final_mask = cv2.bilateralFilter(final_mask, 5, 50, 50)
            print("✨ Applied edge smoothing")
        
        # Create final image
        final_alpha = Image.fromarray(final_mask)
        r, g, b = original_image.split()
        result_image = Image.merge("RGBA", (r, g, b, final_alpha))
        
        # Save result
        result_image.save(output_path, 'PNG', optimize=True)
        
        print(f"✅ Success! Advanced avatar processing complete")
        print(f"💾 Saved to: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_advanced_presets():
    """Create advanced preset configurations"""
    
    presets = {
        'max_preserve': {
            'use_consensus': True,
            'preserve_strength': 0.9,
            'detail_preservation': True,
            'safe_mode': True,
            'description': 'Maximum preservation - safest option'
        },
        'balanced': {
            'use_consensus': True,
            'preserve_strength': 0.7,
            'detail_preservation': True,
            'safe_mode': False,
            'description': 'Balanced quality and preservation'
        },
        'fast_safe': {
            'use_consensus': False,
            'preserve_strength': 0.8,
            'detail_preservation': True,
            'safe_mode': True,
            'description': 'Fast single model with safety features'
        },
        'quality': {
            'use_consensus': True,
            'preserve_strength': 0.6,
            'detail_preservation': True,
            'safe_mode': False,
            'description': 'Best quality result'
        }
    }
    
    return presets

def main():
    print("🎭 Advanced Avatar Detail Preservation Tool")
    print("=" * 55)
    
    if len(sys.argv) < 3:
        print("Usage: python advanced_avatar_removal.py input output [preset]")
        print("\n🛡️  Advanced presets:")
        presets = create_advanced_presets()
        for name, config in presets.items():
            print(f"  {name:12} - {config['description']}")
        print("\n💡 Examples:")
        print("  python advanced_avatar_removal.py avatar.jpg result.png")
        print("  python advanced_avatar_removal.py avatar.jpg result.png max_preserve")
        print("  python advanced_avatar_removal.py avatar.jpg result.png balanced")
        return
    
    input_image = sys.argv[1]
    output_image = sys.argv[2]
    preset_name = sys.argv[3] if len(sys.argv) > 3 else 'max_preserve'
    
    presets = create_advanced_presets()
    
    if preset_name not in presets:
        print(f"❌ Unknown preset: {preset_name}")
        print(f"Available presets: {', '.join(presets.keys())}")
        return
    
    preset = presets[preset_name]
    print(f"🎨 Using preset: {preset_name} - {preset['description']}")
    
    success = advanced_avatar_removal(
        input_image, output_image,
        use_consensus=preset['use_consensus'],
        preserve_strength=preset['preserve_strength'],
        detail_preservation=preset['detail_preservation'],
        safe_mode=preset['safe_mode']
    )
    
    if success:
        print("\n🎉 Processing completed successfully!")
        print("💡 This tool is designed to prevent losing any parts of your avatar/model")
    else:
        print("\n❌ Processing failed")

if __name__ == "__main__":
    main()
