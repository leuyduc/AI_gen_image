import os
import time
import logging
import base64
import io
from typing import Optional, Tuple, Dict, Any, Union
from pathlib import Path

import requests
from PIL import Image

from core.settings import AI_API_KEY, API_PROVIDER, DEFAULT_IMAGE_SIZE, APP_CONFIG

logger = logging.getLogger(__name__)

class APIClient:
    """Client for interacting with AI image generation APIs."""
    
    def __init__(self, api_key: str = None, provider: str = None):
        # Try to get values from config first, then from parameters, then from globals
        self.api_key = api_key or APP_CONFIG.get("api_key", AI_API_KEY)
        self.provider = (provider or APP_CONFIG.get("api_provider", API_PROVIDER)).lower()
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
        if not self.api_key:
            logger.warning("No API key provided. Set API key in Settings.")
    
    def generate_image(self, 
                      prompt: str, 
                      size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
                      negative_prompt: str = None) -> Optional[Image.Image]:
        """Generate an image based on text prompt using the selected provider."""
        if not self.api_key:
            logger.error("API key is required")
            return None
        
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                if self.provider == "openai":
                    return self._call_openai(prompt, size)
                elif self.provider == "stability":
                    return self._call_stability(prompt, size, negative_prompt)
                elif self.provider == "gemini":
                    return self._call_gemini(prompt, size)
                else:
                    logger.error(f"Unsupported API provider: {self.provider}")
                    return None
            except Exception as e:
                retry_count += 1
                wait_time = self.retry_delay * (2 ** (retry_count - 1))  # Exponential backoff
                
                logger.warning(f"API call failed ({retry_count}/{self.max_retries}): {str(e)}")
                logger.info(f"Retrying in {wait_time} seconds...")
                
                time.sleep(wait_time)
        
        logger.error(f"Failed to generate image after {self.max_retries} attempts")
        return None
    
    def _call_openai(self, prompt: str, size: Tuple[int, int]) -> Optional[Image.Image]:
        """Call OpenAI's DALL-E API."""
        logger.info(f"Calling OpenAI DALL-E with prompt: {prompt[:50]}...")
        
        # Convert size to OpenAI format (e.g. 512x512)
        size_str = f"{size[0]}x{size[1]}"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "prompt": prompt,
            "size": size_str,
            "n": 1,
            "response_format": "b64_json"
        }
        
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
            raise Exception(f"API request failed with status {response.status_code}")
        
        response_data = response.json()
        image_data = base64.b64decode(response_data["data"][0]["b64_json"])
        
        return Image.open(io.BytesIO(image_data))
    
    def _call_stability(self, 
                        prompt: str, 
                        size: Tuple[int, int],
                        negative_prompt: str = None) -> Optional[Image.Image]:
        """Call Stability AI API."""
        logger.info(f"Calling Stability AI with prompt: {prompt[:50]}...")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1.0
                }
            ],
            "height": size[1],
            "width": size[0],
            "samples": 1,
            "cfg_scale": 7.0,
            "steps": 30,
            "style_preset": "photographic"
        }
        
        # Add negative prompt if provided
        if negative_prompt:
            payload["text_prompts"].append({
                "text": negative_prompt,
                "weight": -1.0
            })
        
        response = requests.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            logger.error(f"Stability API error: {response.status_code} - {response.text}")
            raise Exception(f"API request failed with status {response.status_code}")
        
        response_data = response.json()
        image_data = base64.b64decode(response_data["artifacts"][0]["base64"])
        
        return Image.open(io.BytesIO(image_data))
        
    def _call_gemini(self, prompt: str, size: Tuple[int, int]) -> Optional[Image.Image]:
        """Call Google's Gemini API for image generation."""
        logger.info(f"Calling Gemini API with prompt: {prompt[:50]}...")
        
        # Convert size to match Gemini requirements
        # We'll choose the closest supported size
        supported_sizes = {
            "1024x1024": (1024, 1024),
            "1024x1792": (1024, 1792),
            "1792x1024": (1792, 1024)
        }
        
        # Find best fit size
        if size[0] == size[1]:  # Square image
            size_key = "1024x1024"
        elif size[0] < size[1]:  # Portrait
            size_key = "1024x1792"
        else:  # Landscape
            size_key = "1792x1024"
            
        actual_size = supported_sizes[size_key]
        logger.info(f"Using Gemini size: {size_key} (requested: {size[0]}x{size[1]})")
        
        # Build the API URL with key - Using gemini-1.5-flash model
        api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": f"Generate an image based on this description: {prompt}"
                        }
                    ]
                }
            ],
            "generation_config": {
                "temperature": 0.7,
                "topP": 0.95,
                "topK": 40
            }
        }
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            logger.error(f"Gemini API error: {response.status_code} - {response.text}")
            raise Exception(f"API request failed with status {response.status_code}")
        
        response_data = response.json()
        
        # Extract image data from the response
        try:
            # Gemini might return the image in various formats
            for candidate in response_data.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    if "inlineData" in part:
                        mime_type = part["inlineData"]["mimeType"]
                        if mime_type.startswith("image/"):
                            image_data = base64.b64decode(part["inlineData"]["data"])
                            return Image.open(io.BytesIO(image_data))
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            raise Exception(f"Failed to extract image from Gemini response: {str(e)}")
        
        raise Exception("No image found in Gemini response")

    @staticmethod
    def save_image(image: Image.Image, save_dir: Path, prompt: str) -> str:
        """Save the generated image to disk."""
        if not save_dir.exists():
            save_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a filename based on the first few words of the prompt
        clean_prompt = "".join(c if c.isalnum() else "_" for c in prompt[:30])
        timestamp = int(time.time())
        filename = f"{clean_prompt}_{timestamp}.png"
        file_path = save_dir / filename
        
        # Save the image
        image.save(file_path, format="PNG")
        logger.info(f"Image saved to {file_path}")
        
        return str(file_path) 