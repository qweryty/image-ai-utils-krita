import json
from enum import Enum
from typing import Optional, List, Tuple, Callable

import httpx
from PIL import Image
from websocket import create_connection
from .settings import Settings
from .utils import base64url_to_image, image_to_base64url


# TODO check response code and throw custom exception
class ImageAIUtilsClient:
    class WebSocketResponseStatus(str, Enum):
        FINISHED = 'finished'
        PROGRESS = 'progress'

    def __init__(self, base_url: str, username: str, password: str, use_tls: bool = False):
        if not base_url.endswith('/'):
            base_url += '/'

        base_url = base_url.replace('http://', '')
        base_url = base_url.replace('https://', '')

        if use_tls:
            self._base_http_url = 'https://' + base_url
            self._base_websocket_url = 'wss://' + base_url
        else:
            self._base_http_url = 'http://' + base_url
            self._base_websocket_url = 'ws://' + base_url

        self._default_headers = {
            'Accept-Encoding': 'gzip,deflate'
        }
        self._auth = (username, password)

    def text_to_image(
            self,
            prompt: str,
            aspect_ratio: float,
            num_variants: int = 6,
            num_inference_steps: int = 50,
            guidance_scale: float = 7.5,
            seed: Optional[int] = None,
            progress_callback: Optional[Callable[[float], None]] = None
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

        connection = create_connection(self._base_websocket_url + 'text_to_image')
        connection.send(json.dumps({'username': self._auth[0], 'password': self._auth[1]}))
        connection.send(json.dumps(request_data))

        response = json.loads(connection.recv())
        while response['status'] != self.WebSocketResponseStatus.FINISHED:
            if response['status'] == self.WebSocketResponseStatus.PROGRESS:
                progress_callback(response['progress'])

            response = json.loads(connection.recv())

        images = response['result']['images']
        return [base64url_to_image(image.encode()) for image in images]

    def image_to_image(
            self,
            prompt: str,
            source_image: Image.Image,
            strength: float = 0.8,
            num_variants: int = 6,
            num_inference_steps: int = 50,
            guidance_scale: float = 7.5,
            seed: Optional[int] = None,
            progress_callback: Optional[Callable[[float], None]] = None
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

        connection = create_connection(self._base_websocket_url + 'image_to_image')
        connection.send(json.dumps({'username': self._auth[0], 'password': self._auth[1]}))
        connection.send(json.dumps(request_data))

        response = json.loads(connection.recv())
        while response['status'] != self.WebSocketResponseStatus.FINISHED:
            if response['status'] == self.WebSocketResponseStatus.PROGRESS:
                progress_callback(response['progress'])

            response = json.loads(connection.recv())

        images = response['result']['images']
        return [base64url_to_image(image.encode()) for image in images]

    def inpaint(
            self,
            prompt: str,
            source_image: Image.Image,
            mask: Optional[Image.Image],
            strength: float = 0.8,
            num_variants: int = 6,
            num_inference_steps: int = 50,
            guidance_scale: float = 7.5,
            seed: Optional[int] = None,
            progress_callback: Optional[Callable[[float], None]] = None
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
        if mask is not None:
            request_data['mask'] = image_to_base64url(mask).decode()
        if seed is not None:
            request_data['seed'] = seed

        connection = create_connection(self._base_websocket_url + 'inpainting')
        connection.send(json.dumps({'username': self._auth[0], 'password': self._auth[1]}))
        connection.send(json.dumps(request_data))

        response = json.loads(connection.recv())
        while response['status'] != self.WebSocketResponseStatus.FINISHED:
            if response['status'] == self.WebSocketResponseStatus.PROGRESS:
                progress_callback(response['progress'])

            response = json.loads(connection.recv())

        images = response['result']['images']
        return [base64url_to_image(image.encode()) for image in images]

    def upscale(
            self,
            source_image: Image.Image,
            target_width: int,
            target_height: int
    ) -> Image.Image:
        request_data = {
            'image': image_to_base64url(source_image).decode(),
            'target_width': target_width,
            'target_height': target_height,
        }

        response = httpx.post(
            self._base_http_url + 'upscale',
            json=request_data,
            headers=self._default_headers,
            timeout=None,
            auth=self._auth
        )
        return base64url_to_image(response.json()['image'].encode())

    def test_connection(self) -> Tuple[bool, str]:
        try:
            response = httpx.get(
                self._base_http_url + 'ping', headers=self._default_headers, auth=self._auth
            )
            return response.status_code == httpx.codes.OK, response.text
        except Exception as e:
            return False, f'Exception: {type(e)}'

    _client = None

    @classmethod
    def client(cls):
        if cls._client is not None:
            return cls._client

        if Settings.settings() is None:
            return None

        cls._client = ImageAIUtilsClient(
            base_url=Settings.settings().SERVER_URL,
            use_tls=Settings.settings().USE_TLS,
            username=Settings.settings().USERNAME,
            password=Settings.settings().PASSWORD
        )

        return cls._client
