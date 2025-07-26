#!/usr/bin/env python3
"""
Background Removal Comparison Tool
Creates multiple versions with different sharpness levels
"""

import sys
import os
from bg_remove_final import remove_bg_ultimate

def create_all_versions(input_path):
    """
    Create all versions of background removal for comparison
    """
    if not os.path.exists(input_path):
        print(f"❌ Error: Input file '{input_path}' not found")
        return False
    
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    versions = {
        'binary': f"{base_name}_binary.png",
        'sharp': f"{base_name}_sharp.png", 
        'clean': f"{base_name}_clean.png",
        'soft': f"{base_name}_soft.png"
    }
    
    print("🚀 Creating all background removal versions...")
    print("=" * 50)
    
    success_count = 0
    for mode, output_file in versions.items():
        print(f"\n📸 Creating {mode} version...")
        if remove_bg_ultimate(input_path, output_file, mode):
            success_count += 1
        else:
            print(f"❌ Failed to create {mode} version")
    
    print(f"\n🎉 Completed! Created {success_count}/{len(versions)} versions")
    print("\n📋 Results:")
    for mode, output_file in versions.items():
        if os.path.exists(output_file):
            print(f"  ✅ {mode:6} -> {output_file}")
        else:
            print(f"  ❌ {mode:6} -> Failed")
    
    print("\n💡 Recommendations:")
    print("  • Use 'binary' for logos, icons, or graphics requiring hard edges")
    print("  • Use 'sharp' for photos where you want minimal soft edges")
    print("  • Use 'clean' for balanced results with natural-looking edges")
    print("  • Use 'soft' to preserve original anti-aliasing")
    
    return success_count == len(versions)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Background Removal Comparison Tool")
        print("=" * 40)
        print("Usage: python compare_versions.py input_image")
        print("\nThis will create 4 versions:")
        print("  • input_binary.png - Hard edges, no anti-aliasing")
        print("  • input_sharp.png  - Sharp edges, minimal blur")
        print("  • input_clean.png  - Balanced result")
        print("  • input_soft.png   - Soft edges preserved")
        print("\nExample:")
        print("  python compare_versions.py photo.jpg")
        sys.exit(1)
    
    input_image = sys.argv[1]
    create_all_versions(input_image)
