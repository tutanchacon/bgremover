"""
Utility functions for the bgremover package
"""
import os
from PIL import Image
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Supported image formats
SUPPORTED_INPUT_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
SUPPORTED_OUTPUT_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}


def validate_image(image_path: str) -> Tuple[bool, str]:
    """
    Validate if an image file exists and is supported.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not os.path.exists(image_path):
        return False, f"File not found: {image_path}"
    
    if not os.path.isfile(image_path):
        return False, f"Path is not a file: {image_path}"
    
    file_extension = os.path.splitext(image_path)[1].lower()
    if file_extension not in SUPPORTED_INPUT_FORMATS:
        return False, f"Unsupported format: {file_extension}. Supported: {', '.join(SUPPORTED_INPUT_FORMATS)}"
    
    try:
        with Image.open(image_path) as img:
            img.verify()
        return True, ""
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"


def get_supported_formats() -> dict:
    """
    Get lists of supported input and output formats.
    
    Returns:
        dict: Dictionary with 'input' and 'output' format lists
    """
    return {
        'input': sorted(list(SUPPORTED_INPUT_FORMATS)),
        'output': sorted(list(SUPPORTED_OUTPUT_FORMATS))
    }


def ensure_output_dir(output_path: str) -> bool:
    """
    Ensure the output directory exists.
    
    Args:
        output_path: Path to the output file
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        return True
    except Exception as e:
        logger.error(f"Failed to create output directory: {e}")
        return False


def get_optimal_output_format(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Determine the optimal output format based on input.
    
    Args:
        input_path: Input image path
        output_path: Optional output path
        
    Returns:
        str: Recommended file extension
    """
    # If output path is specified, use its extension
    if output_path:
        output_ext = os.path.splitext(output_path)[1].lower()
        if output_ext in SUPPORTED_OUTPUT_FORMATS:
            return output_ext
    
    # For background removal, PNG is almost always optimal due to transparency
    return '.png'


def calculate_image_stats(image_path: str) -> dict:
    """
    Calculate basic statistics for an image.
    
    Args:
        image_path: Path to image file
        
    Returns:
        dict: Image statistics
    """
    try:
        with Image.open(image_path) as img:
            file_size = os.path.getsize(image_path)
            
            stats = {
                'filename': os.path.basename(image_path),
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.width,
                'height': img.height,
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'aspect_ratio': round(img.width / img.height, 2),
                'total_pixels': img.width * img.height
            }
            
            # Add transparency info for RGBA images
            if img.mode == 'RGBA':
                import numpy as np
                alpha_channel = np.array(img)[:,:,3]
                transparent_pixels = np.sum(alpha_channel == 0)
                partial_transparent = np.sum((alpha_channel > 0) & (alpha_channel < 255))
                opaque_pixels = np.sum(alpha_channel == 255)
                
                stats.update({
                    'has_transparency': True,
                    'transparent_pixels': int(transparent_pixels),
                    'partial_transparent_pixels': int(partial_transparent),
                    'opaque_pixels': int(opaque_pixels),
                    'transparency_percentage': round((transparent_pixels / stats['total_pixels']) * 100, 2)
                })
            else:
                stats.update({
                    'has_transparency': False,
                    'transparent_pixels': 0,
                    'partial_transparent_pixels': 0,
                    'opaque_pixels': stats['total_pixels'],
                    'transparency_percentage': 0.0
                })
            
            return stats
            
    except Exception as e:
        logger.error(f"Error calculating image stats: {e}")
        return {'error': str(e)}


def batch_process_images(
    input_dir: str, 
    output_dir: str, 
    remover_instance, 
    **kwargs
) -> List[dict]:
    """
    Process multiple images in a directory.
    
    Args:
        input_dir: Directory containing input images
        output_dir: Directory to save processed images
        remover_instance: BackgroundRemover instance
        **kwargs: Additional arguments for remove_background method
        
    Returns:
        List[dict]: Results for each processed image
    """
    results = []
    
    if not os.path.exists(input_dir):
        logger.error(f"Input directory not found: {input_dir}")
        return results
    
    # Ensure output directory exists
    ensure_output_dir(output_dir)
    
    # Process all supported images in directory
    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)
        
        # Skip non-files
        if not os.path.isfile(file_path):
            continue
        
        # Check if file is supported
        is_valid, error_msg = validate_image(file_path)
        if not is_valid:
            results.append({
                'input_file': filename,
                'success': False,
                'error': error_msg
            })
            continue
        
        # Generate output path
        name_without_ext = os.path.splitext(filename)[0]
        output_path = os.path.join(output_dir, f"{name_without_ext}_no_bg.png")
        
        # Process image
        try:
            success = remover_instance.remove_background(file_path, output_path, **kwargs)
            results.append({
                'input_file': filename,
                'output_file': os.path.basename(output_path),
                'input_path': file_path,
                'output_path': output_path,
                'success': success
            })
        except Exception as e:
            results.append({
                'input_file': filename,
                'success': False,
                'error': str(e)
            })
    
    return results


def create_comparison_image(original_path: str, processed_path: str, output_path: str) -> bool:
    """
    Create a side-by-side comparison image.
    
    Args:
        original_path: Path to original image
        processed_path: Path to processed image
        output_path: Path to save comparison image
        
    Returns:
        bool: True if successful
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Load images
        original = Image.open(original_path).convert('RGBA')
        processed = Image.open(processed_path).convert('RGBA')
        
        # Resize to same height if different
        if original.height != processed.height:
            target_height = min(original.height, processed.height)
            original = original.resize((
                int(original.width * target_height / original.height),
                target_height
            ), Image.Resampling.LANCZOS)
            processed = processed.resize((
                int(processed.width * target_height / processed.height),
                target_height
            ), Image.Resampling.LANCZOS)
        
        # Create comparison image
        total_width = original.width + processed.width + 20  # 20px gap
        comparison = Image.new('RGBA', (total_width, original.height), (255, 255, 255, 255))
        
        # Paste images
        comparison.paste(original, (0, 0))
        comparison.paste(processed, (original.width + 20, 0))
        
        # Add labels
        draw = ImageDraw.Draw(comparison)
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 10), "Original", fill=(0, 0, 0, 255), font=font)
        draw.text((original.width + 30, 10), "Processed", fill=(0, 0, 0, 255), font=font)
        
        # Save comparison
        comparison.save(output_path, format='PNG')
        logger.info(f"Comparison saved to: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating comparison image: {e}")
        return False
