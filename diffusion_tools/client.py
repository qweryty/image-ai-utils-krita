import os
from typing import Optional, List

import httpx
from PIL import Image
from .ui.utils import base64url_to_image, image_to_base64url


# TODO check response code and throw custom exception
class DiffusionClient:
    def __init__(self, base_url: str):
        self._base_url = base_url
        self._default_headers = {
            'Accept-Encoding': 'gzip,deflate'
        }

    def text_to_image(
            self,
            prompt: str,
            aspect_ratio: float,
            num_variants: int = 6,
            num_inference_steps: int = 50,
            guidance_scale: float = 7.5,
            seed: Optional[int] = None,
    ) -> List[Image.Image]:
        request_data = {
            'prompt': prompt,
            'num_inference_steps': num_inference_steps,
            'guidance_scale': guidance_scale,
            'num_variants': num_variants,
            'output_format': 'PNG',
            'aspect_ratio': aspect_ratio,
        }
        if seed is not None:
            request_data['seed'] = seed

        response = httpx.post(
            self._base_url + 'text_to_image',
            json=request_data,
            headers=self._default_headers,
            timeout=None
        )
        return [base64url_to_image(image.encode()) for image in response.json()['images']]

    def image_to_image(
            self,
            prompt: str,
            source_image: Image.Image,
            strength: float = 0.8,
            num_variants: int = 6,
            num_inference_steps: int = 50,
            guidance_scale: float = 7.5,
            seed: Optional[int] = None,
    ) -> List[Image.Image]:
        request_data = {
            'prompt': prompt,
            'source_image': image_to_base64url(source_image).decode(),
            'strength': strength,
            'num_inference_steps': num_inference_steps,
            'guidance_scale': guidance_scale,
            'num_variants': num_variants,
            'output_format': 'PNG',
        }
        if seed is not None:
            request_data['seed'] = seed

        response = httpx.post(
            self._base_url + 'image_to_image',
            json=request_data,
            headers=self._default_headers,
            timeout=None
        )
        print(response)
        return [base64url_to_image(image.encode()) for image in response.json()['images']]

    def inpaint(
            self,
            prompt: str,
            source_image: Image.Image,
            mask: Image.Image,
            strength: float = 0.8,
            num_variants: int = 6,
            num_inference_steps: int = 50,
            guidance_scale: float = 7.5,
            seed: Optional[int] = None,
    ) -> List[Image.Image]:
        request_data = {
            'prompt': prompt,
            'source_image': image_to_base64url(source_image).decode(),
            'mask': image_to_base64url(mask).decode(),
            'strength': strength,
            'num_inference_steps': num_inference_steps,
            'guidance_scale': guidance_scale,
            'num_variants': num_variants,
            'output_format': 'PNG',
        }
        if seed is not None:
            request_data['seed'] = seed

        response = httpx.post(
            self._base_url + 'image_to_image',
            json=request_data,
            headers=self._default_headers,
            timeout=None
        )
        print(response)
        return [base64url_to_image(image.encode()) for image in response.json()['images']]


diffusion_client = DiffusionClient(os.environ.get('AI_IMAGE_UTILS_URL', 'http://localhost:8000/'))
