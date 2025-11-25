import base64
import os
import io
import time
from pathlib import Path
from PIL import Image

def compress_image_for_api(image_path: str) -> str:
    """
    Compress image to fit under Anthropic's 5MB limit
    Returns base64 string of compressed image
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Try different compression levels
            for quality in [85, 70, 60, 50]:
                # Save to memory buffer
                buffer = io.BytesIO()
                img.save(buffer, format='PNG', quality=quality, optimize=True)
                
                if buffer.tell() <= 5 * 1024 * 1024:  # 5MB limit
                    buffer.seek(0)
                    compressed_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    return compressed_b64
            
            # If still too large, resize
            width, height = img.size
            new_size = (int(width * 0.6), int(height * 0.6))
            img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            img_resized.save(buffer, format='JPEG', quality=60, optimize=True)
            buffer.seek(0)
            compressed_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return compressed_b64
            
    except Exception as e:
        # Fallback: try original image
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

def find_equipment_images(pmt_number: str, image_dir: str = 'converted_to_image') -> list:
    """
    Find all PNG images for a given PMT number with flexible matching
    """
    image_files = []
    current_dir = Path(image_dir)
    
    # Remove spaces and special characters for flexible matching
    clean_pmt = pmt_number.replace(' ', '').replace('-', '').replace('_', '').lower()
    
    for pattern in ['*.png', '*.jpg', '*.jpeg']:
        for file_path in current_dir.rglob(pattern):
            clean_filename = file_path.stem.replace(' ', '').replace('-', '').replace('_', '').lower()
            
            if clean_pmt in clean_filename:
                image_files.append(file_path)
    
    # Remove duplicates
    image_files = list(set(image_files))
    image_files.sort()
    
    return image_files