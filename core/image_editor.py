import logging
from PIL import Image, ImageOps
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class ImageEditor:
    """Provides image manipulation functions like crop, rotate, and flip."""
    
    @staticmethod
    def crop_image(image: Image.Image, box: Tuple[int, int, int, int]) -> Image.Image:
        """
        Crop an image using the specified box coordinates.
        
        Args:
            image: PIL Image object
            box: Tuple (left, top, right, bottom) coordinates
            
        Returns:
            Cropped PIL Image
        """
        try:
            # Ensure box values are valid
            width, height = image.size
            left, top, right, bottom = box
            
            # Validate crop dimensions
            if left < 0 or top < 0 or right > width or bottom > height:
                logger.warning(f"Invalid crop dimensions: {box} for image size {image.size}")
                # Adjust to valid dimensions
                left = max(0, left)
                top = max(0, top)
                right = min(width, right)
                bottom = min(height, bottom)
            
            if left >= right or top >= bottom:
                logger.error("Invalid crop dimensions: left >= right or top >= bottom")
                return image
            
            return image.crop(box=(left, top, right, bottom))
        except Exception as e:
            logger.error(f"Error cropping image: {e}")
            return image
    
    @staticmethod
    def rotate_image(image: Image.Image, angle: int, expand: bool = True) -> Image.Image:
        """
        Rotate an image by a specified angle.
        
        Args:
            image: PIL Image object
            angle: Rotation angle in degrees (counter-clockwise)
            expand: Whether to expand the output image to fit the rotated image
            
        Returns:
            Rotated PIL Image
        """
        try:
            # Normalize angle to be a multiple of 90 for lossless rotation
            normalized_angle = angle % 360
            
            # For angles that are multiples of 90, use transpose for lossless rotation
            if normalized_angle == 90:
                return image.transpose(Image.ROTATE_90)
            elif normalized_angle == 180:
                return image.transpose(Image.ROTATE_180)
            elif normalized_angle == 270:
                return image.transpose(Image.ROTATE_270)
            else:
                # For other angles, use regular rotation
                return image.rotate(angle, expand=expand, resample=Image.BICUBIC)
        except Exception as e:
            logger.error(f"Error rotating image: {e}")
            return image
    
    @staticmethod
    def flip_image_horizontal(image: Image.Image) -> Image.Image:
        """
        Flip an image horizontally (left to right).
        
        Args:
            image: PIL Image object
            
        Returns:
            Flipped PIL Image
        """
        try:
            return ImageOps.mirror(image)
        except Exception as e:
            logger.error(f"Error flipping image horizontally: {e}")
            return image
    
    @staticmethod
    def flip_image_vertical(image: Image.Image) -> Image.Image:
        """
        Flip an image vertically (top to bottom).
        
        Args:
            image: PIL Image object
            
        Returns:
            Flipped PIL Image
        """
        try:
            return ImageOps.flip(image)
        except Exception as e:
            logger.error(f"Error flipping image vertically: {e}")
            return image
    
    @staticmethod
    def resize_image(image: Image.Image, width: int, height: int) -> Image.Image:
        """
        Resize an image to the specified dimensions.
        
        Args:
            image: PIL Image object
            width: Target width in pixels
            height: Target height in pixels
            
        Returns:
            Resized PIL Image
        """
        try:
            return image.resize((width, height), Image.LANCZOS)
        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            return image
    
    @staticmethod
    def adjust_brightness(image: Image.Image, factor: float) -> Image.Image:
        """
        Adjust image brightness.
        
        Args:
            image: PIL Image object
            factor: Brightness factor (0.0 to 2.0, 1.0 is original brightness)
            
        Returns:
            Brightness-adjusted PIL Image
        """
        try:
            return ImageOps.brightness(image, factor)
        except Exception as e:
            logger.error(f"Error adjusting brightness: {e}")
            return image 