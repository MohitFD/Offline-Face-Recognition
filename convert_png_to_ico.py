"""
Convert PNG to ICO format for Inno Setup installer icon
Usage: python convert_png_to_ico.py
"""
import os
import sys
from PIL import Image

def convert_png_to_ico(png_path, ico_path=None):
    """Convert PNG image to ICO format with multiple sizes"""
    if not os.path.exists(png_path):
        print(f"Error: PNG file not found: {png_path}")
        return False
    
    if ico_path is None:
        ico_path = png_path.replace('.png', '.ico')
    
    try:
        # Open the PNG image
        img = Image.open(png_path)
        
        # Convert to RGBA if not already (for transparency support)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create ICO file with multiple sizes (Windows standard sizes)
        # ICO format supports multiple sizes in one file
        sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        
        # Create list of images at different sizes
        images = []
        for size in sizes:
            # Resize image maintaining aspect ratio
            resized = img.resize(size, Image.Resampling.LANCZOS)
            images.append(resized)
        
        # Save as ICO with all sizes
        img.save(ico_path, format='ICO', sizes=[(s.width, s.height) for s in images])
        
        print(f"Successfully converted {png_path} to {ico_path}")
        print(f"ICO file contains sizes: {[f'{s.width}x{s.height}' for s in images]}")
        return True
        
    except ImportError:
        print("Error: PIL/Pillow is not installed.")
        print("Install it using: pip install Pillow")
        return False
    except Exception as e:
        print(f"Error converting image: {e}")
        return False

if __name__ == "__main__":
    png_file = "fix_hr_prod_logo.png"
    
    if len(sys.argv) > 1:
        png_file = sys.argv[1]
    
    if convert_png_to_ico(png_file):
        print("\nIcon conversion completed!")
        print("You can now use fix_hr_prod_logo.ico in your Inno Setup script.")
    else:
        print("\nIcon conversion failed!")
        sys.exit(1)

