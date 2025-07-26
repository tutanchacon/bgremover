#!/usr/bin/env python3
"""
Avatar Model Comparison Tool
Compare different U²-Net models to find the best one for your avatars
"""

import sys
import os
from u2net_avatar_remover import remove_background_u2net_avatar

def compare_u2net_models(input_path, output_prefix="comparison"):
    """
    Create multiple versions using different U²-Net models for comparison
    
    Args:
        input_path (str): Path to input image
        output_prefix (str): Prefix for output files
    """
    
    if not os.path.exists(input_path):
        print(f"❌ Error: Input file '{input_path}' not found")
        return False
    
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    # Different model configurations optimized for avatars
    model_configs = {
        'u2net_standard': {
            'model_type': 'u2net',
            'preserve_details': True,
            'detail_enhancement': True,
            'edge_refinement': True,
            'mask_threshold': 'adaptive',
            'description': 'U²-Net standard with detail preservation'
        },
        'u2net_human': {
            'model_type': 'u2net_human_seg',
            'preserve_details': True,
            'detail_enhancement': True,
            'edge_refinement': True,
            'mask_threshold': 'conservative',
            'description': 'U²-Net human segmentation (best for people)'
        },
        'silueta_detailed': {
            'model_type': 'silueta',
            'preserve_details': True,
            'detail_enhancement': True,
            'edge_refinement': True,
            'mask_threshold': 'adaptive',
            'description': 'Silueta model with maximum detail preservation'
        },
        'u2net_conservative': {
            'model_type': 'u2net',
            'preserve_details': True,
            'detail_enhancement': False,
            'edge_refinement': False,
            'mask_threshold': 'conservative',
            'description': 'Conservative approach to avoid removing subject parts'
        },
        'u2net_clean': {
            'model_type': 'u2net',
            'preserve_details': False,
            'detail_enhancement': False,
            'edge_refinement': True,
            'mask_threshold': 'otsu',
            'description': 'Clean cutout with automatic thresholding'
        }
    }
    
    print("🎭 Creating U²-Net model comparisons for avatars...")
    print("=" * 60)
    
    success_count = 0
    results = {}
    
    for config_name, config in model_configs.items():
        output_file = f"{output_prefix}_{config_name}.png"
        print(f"\n🔄 Processing: {config_name}")
        print(f"📝 {config['description']}")
        
        try:
            success = remove_background_u2net_avatar(
                input_path, output_file,
                model_type=config['model_type'],
                preserve_details=config['preserve_details'],
                detail_enhancement=config['detail_enhancement'],
                edge_refinement=config['edge_refinement'],
                mask_threshold=config['mask_threshold']
            )
            
            if success:
                success_count += 1
                results[config_name] = {
                    'file': output_file,
                    'description': config['description'],
                    'status': 'SUCCESS'
                }
                print(f"✅ Created: {output_file}")
            else:
                results[config_name] = {
                    'file': output_file,
                    'description': config['description'],
                    'status': 'FAILED'
                }
                print(f"❌ Failed: {config_name}")
                
        except Exception as e:
            print(f"❌ Error with {config_name}: {e}")
            results[config_name] = {
                'file': output_file,
                'description': config['description'],
                'status': f'ERROR: {str(e)}'
            }
    
    # Print summary
    print(f"\n🎉 Completed! Created {success_count}/{len(model_configs)} comparisons")
    print("\n📋 Results Summary:")
    print("-" * 60)
    
    for config_name, result in results.items():
        status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
        print(f"{status_icon} {config_name:18} -> {result['file']}")
        print(f"   {result['description']}")
        print()
    
    # Recommendations
    print("💡 Recommendations for avatars:")
    print("  • u2net_human     - Best for portrait avatars and people")
    print("  • silueta_detailed - Maximum detail preservation")
    print("  • u2net_conservative - If parts of avatar are being removed")
    print("  • u2net_standard  - Good general purpose option")
    print("  • u2net_clean     - For clean, simple cutouts")
    
    return success_count > 0

def analyze_avatar_issues(input_path):
    """
    Analyze potential issues with avatar processing
    """
    from PIL import Image
    import numpy as np
    
    try:
        img = Image.open(input_path)
        img_array = np.array(img)
        
        print(f"\n🔍 Avatar Analysis for: {input_path}")
        print("-" * 40)
        print(f"📏 Dimensions: {img.size[0]} x {img.size[1]} pixels")
        print(f"🎨 Mode: {img.mode}")
        print(f"📊 Channels: {len(img.getbands())}")
        
        # Check image characteristics
        if img.size[0] < 512 or img.size[1] < 512:
            print("⚠️  Small image - may lose fine details")
        
        # Check contrast
        if img.mode == 'RGB':
            gray = img.convert('L')
            hist = gray.histogram()
            contrast = np.std(hist)
            if contrast < 2000:
                print("⚠️  Low contrast - may affect separation quality")
        
        # Check aspect ratio
        aspect_ratio = img.size[0] / img.size[1]
        if aspect_ratio > 2 or aspect_ratio < 0.5:
            print("⚠️  Unusual aspect ratio - check for cropping issues")
        
        print("✅ Analysis complete")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Avatar Model Comparison Tool")
        print("=" * 40)
        print("Usage: python avatar_model_comparison.py input_image [output_prefix]")
        print("\nThis will create multiple versions using different U²-Net models:")
        print("  • u2net_standard    - Standard U²-Net with enhancements")
        print("  • u2net_human       - Human segmentation model")
        print("  • silueta_detailed  - Silueta with detail preservation")
        print("  • u2net_conservative- Conservative to avoid removing avatar parts")
        print("  • u2net_clean       - Clean cutout approach")
        print("\nExample:")
        print("  python avatar_model_comparison.py avatar.jpg my_avatar")
        print("  (Creates: my_avatar_u2net_standard.png, my_avatar_u2net_human.png, etc.)")
        sys.exit(1)
    
    input_image = sys.argv[1]
    output_prefix = sys.argv[2] if len(sys.argv) > 2 else "avatar_comparison"
    
    # Analyze the input image first
    analyze_avatar_issues(input_image)
    
    # Run the comparison
    compare_u2net_models(input_image, output_prefix)
