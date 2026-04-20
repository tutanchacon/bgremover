#!/usr/bin/env python3
"""
Command Line Interface for BGRemover Package
"""
import argparse
import sys
import os
from typing import Optional

from .core import BackgroundRemover
from .utils import validate_image, ensure_output_dir, get_supported_formats, batch_process_images


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Professional background remover with element preservation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  bgremover input.jpg output.png
  bgremover input.jpg output.png --threshold 20 --verbose
  bgremover input_dir/ output_dir/ --batch
  bgremover input_dir/ output_dir/ --batch --recursive
  bgremover input.png --stats
        """
    )
    
    # Input/Output arguments
    parser.add_argument("input", help="Input image file or directory (for batch processing)")
    parser.add_argument("output", nargs='?', help="Output image file or directory")
    
    # Processing options
    parser.add_argument(
        "-t", "--threshold", 
        type=int, 
        default=50, 
        help="Minimum alpha threshold to preserve elements (0-255, default: 50)"
    )
    parser.add_argument(
        "--no-preserve", 
        action="store_true", 
        help="Disable element preservation"
    )
    parser.add_argument(
        "--no-smooth", 
        action="store_true", 
        help="Disable edge smoothing"
    )
    parser.add_argument(
        "--model", 
        default="isnet-general-use", 
        help="rembg model to use (default: isnet-general-use)"
    )
    
    # Batch processing
    parser.add_argument(
        "--batch", 
        action="store_true", 
        help="Process all images in input directory"
    )
    parser.add_argument(
        "--recursive", 
        action="store_true", 
        help="Process subdirectories recursively (maintains folder structure)"
    )
    
    # Information commands
    parser.add_argument(
        "--stats", 
        action="store_true", 
        help="Show image statistics only (no processing)"
    )
    parser.add_argument(
        "--formats", 
        action="store_true", 
        help="Show supported formats"
    )
    
    # Output options
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Show detailed processing information"
    )
    parser.add_argument(
        "--quiet", 
        action="store_true", 
        help="Suppress all output except errors"
    )
    
    args = parser.parse_args()
    
    # Handle special commands
    if args.formats:
        show_supported_formats()
        return 0
    
    if args.stats:
        return show_image_stats(args.input)
    
    # Validate input
    if not args.input:
        parser.error("Input path is required")
    
    if not args.batch and not args.output:
        parser.error("Output path is required (or use --batch for directory processing)")
    
    # Process images
    try:
        if args.batch:
            return process_batch(args)
        else:
            return process_single(args)
    except KeyboardInterrupt:
        if not args.quiet:
            print("\n⚠️  Processing interrupted by user")
        return 1
    except Exception as e:
        if not args.quiet:
            print(f"❌ Error: {e}")
        return 1


def process_single(args) -> int:
    """Process a single image."""
    # Validate input
    is_valid, error_msg = validate_image(args.input)
    if not is_valid:
        if not args.quiet:
            print(f"❌ Input validation failed: {error_msg}")
        return 1
    
    # Ensure output directory exists
    if not ensure_output_dir(args.output):
        if not args.quiet:
            print(f"❌ Failed to create output directory for: {args.output}")
        return 1
    
    # Initialize remover
    try:
        remover = BackgroundRemover(model_name=args.model)
    except Exception as e:
        if not args.quiet:
            print(f"❌ Failed to initialize background remover: {e}")
        return 1
    
    # Process image
    success = remover.remove_background(
        input_path=args.input,
        output_path=args.output,
        min_alpha_threshold=args.threshold,
        preserve_elements=not args.no_preserve,
        smooth_edges=not args.no_smooth,
        verbose=args.verbose and not args.quiet
    )
    
    if success:
        if not args.quiet:
            print(f"✅ Successfully processed: {args.input} → {args.output}")
        return 0
    else:
        if not args.quiet:
            print(f"❌ Failed to process: {args.input}")
        return 1


def process_batch(args) -> int:
    """Process multiple images in a directory."""
    input_dir = args.input
    output_dir = args.output or f"{input_dir}_processed"
    
    if not os.path.isdir(input_dir):
        if not args.quiet:
            print(f"❌ Input directory not found: {input_dir}")
        return 1
    
    # Initialize remover
    try:
        remover = BackgroundRemover(model_name=args.model)
    except Exception as e:
        if not args.quiet:
            print(f"❌ Failed to initialize background remover: {e}")
        return 1
    
    # Process batch
    results = batch_process_images(
        args.input,
        args.output,
        remover,
        recursive=args.recursive,
        min_alpha_threshold=args.threshold,
        preserve_elements=not args.no_preserve,
        smooth_edges=not args.no_smooth,
        verbose=args.verbose
    )
    
    # Report results
    if not args.quiet:
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        
        print(f"\n📊 Batch processing completed:")
        print(f"   ✅ Successful: {successful}/{total}")
        
        if successful < total:
            print(f"   ❌ Failed: {total - successful}")
            if args.verbose:
                print("\nFailed files:")
                for result in results:
                    if not result['success']:
                        print(f"   - {result['input_file']}: {result.get('error', 'Unknown error')}")
        
        if successful > 0:
            print(f"   📁 Output directory: {output_dir}")
    
    return 0 if results and any(r['success'] for r in results) else 1


def show_image_stats(image_path: str) -> int:
    """Show statistics for an image."""
    from .utils import calculate_image_stats
    
    is_valid, error_msg = validate_image(image_path)
    if not is_valid:
        print(f"❌ {error_msg}")
        return 1
    
    stats = calculate_image_stats(image_path)
    if 'error' in stats:
        print(f"❌ Error reading image: {stats['error']}")
        return 1
    
    print(f"📊 Image Statistics: {stats['filename']}")
    print(f"   📐 Dimensions: {stats['width']} × {stats['height']} pixels")
    print(f"   💾 File size: {stats['file_size_mb']} MB")
    print(f"   🎨 Format: {stats['format']} ({stats['mode']})")
    print(f"   📏 Aspect ratio: {stats['aspect_ratio']}")
    print(f"   🔢 Total pixels: {stats['total_pixels']:,}")
    
    if stats['has_transparency']:
        print(f"   🔍 Transparency: {stats['transparency_percentage']:.1f}% transparent")
        print(f"   👁️  Opaque pixels: {stats['opaque_pixels']:,}")
        print(f"   🌫️  Partial transparent: {stats['partial_transparent_pixels']:,}")
        print(f"   🕳️  Fully transparent: {stats['transparent_pixels']:,}")
    else:
        print(f"   🎯 No transparency channel")
    
    return 0


def show_supported_formats():
    """Show supported file formats."""
    formats = get_supported_formats()
    
    print("🎨 Supported File Formats:")
    print(f"   📥 Input: {', '.join(formats['input'])}")
    print(f"   📤 Output: {', '.join(formats['output'])}")
    print()
    print("💡 Recommendation: Use PNG output for best transparency support")


if __name__ == "__main__":
    sys.exit(main())
