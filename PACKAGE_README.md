# Professional BGRemover Package

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Professional background removal with element preservation. This package provides advanced AI-powered background removal that preserves character elements like accessories, props, and details while removing only the true background.

## 🚀 Quick Start

### Installation

```bash
# From local package
pip install -e .

# From requirements
pip install -r requirements.txt
```

### Command Line Usage

```bash
# Basic usage
bgremover input.jpg output.png

# Advanced options
bgremover input.jpg output.png --threshold 20 --verbose

# Batch processing
bgremover input_folder/ output_folder/ --batch

# Show image statistics
bgremover input.jpg --stats
```

### Python API

```python
from bgremover_package import BackgroundRemover

# Initialize
remover = BackgroundRemover()

# Process single image
success = remover.remove_background('input.jpg', 'output.png')

# With custom settings
success = remover.remove_background(
    'input.jpg', 
    'output.png',
    min_alpha_threshold=20,
    preserve_elements=True,
    verbose=True
)
```

## 🎯 Key Features

- **Element Preservation**: Keeps accessories, props, and character details
- **Smart Transparency**: Converts partial transparencies to fully opaque
- **Professional Quality**: ISNet-based AI segmentation
- **Batch Processing**: Process multiple images at once
- **CLI & API**: Both command-line and programmatic interfaces
- **Format Support**: JPG, PNG, BMP, TIFF, WebP input; PNG, JPG output

## 📖 Advanced Usage

### Threshold Settings

The `min_alpha_threshold` parameter controls what elements are preserved:

- `20` (recommended): Preserves most character elements
- `50` (default): Balanced approach
- `100`: More conservative, removes more potential noise

### Processing Pipeline

1. **AI Segmentation**: ISNet model identifies foreground elements
2. **Transparency Analysis**: Analyzes alpha channel distribution
3. **Element Preservation**: Converts partial transparencies to opaque
4. **Connection**: Links disconnected character elements
5. **Cleanup**: Removes only true background pixels
6. **Smoothing**: Conservative edge smoothing

### Batch Processing

```python
from bgremover_package.utils import batch_process_images

remover = BackgroundRemover()
results = batch_process_images('input_dir/', 'output_dir/', remover)

for result in results:
    print(f"{result['input_file']}: {'✅' if result['success'] else '❌'}")
```

## 🔧 API Reference

### BackgroundRemover Class

```python
class BackgroundRemover:
    def __init__(self, model_name='isnet-general-use')
    
    def remove_background(
        self, 
        input_path: str, 
        output_path: str, 
        min_alpha_threshold: int = 50,
        preserve_elements: bool = True,
        smooth_edges: bool = True,
        verbose: bool = False
    ) -> bool
    
    def get_stats(self, image_path: str) -> dict
```

### Utility Functions

```python
from bgremover_package.utils import (
    validate_image,
    get_supported_formats,
    calculate_image_stats,
    create_comparison_image
)

# Validate input
is_valid, error = validate_image('input.jpg')

# Get format info
formats = get_supported_formats()

# Calculate statistics
stats = calculate_image_stats('image.png')

# Create before/after comparison
create_comparison_image('original.jpg', 'processed.png', 'comparison.png')
```

## 🛠️ Development

### Project Structure

```
bgremover_package/
├── __init__.py          # Package initialization
├── core.py              # Main BackgroundRemover class
├── utils.py             # Utility functions
└── cli.py               # Command-line interface
```

### Dependencies

- **rembg**: AI background removal (ISNet model)
- **OpenCV**: Image processing operations
- **PIL/Pillow**: Image handling and format support
- **NumPy**: Array operations
- **SciPy**: Advanced image processing

## 📊 Performance

- **Quality**: Professional-grade results with element preservation
- **Speed**: Optimized for batch processing
- **Memory**: Efficient handling of large images
- **Compatibility**: Cross-platform (Windows, macOS, Linux)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues, questions, or feature requests:

1. Check existing issues on GitHub
2. Create a new issue with detailed description
3. Include sample images if relevant

---

**Made with ❤️ for professional image processing**
