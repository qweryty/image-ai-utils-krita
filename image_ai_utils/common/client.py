import json
from enum import Enum
from json import JSONDecodeError
from typing import Optional, List, Tuple, Callable, Any, Dict

import httpx
from PIL import Image
from websocket import STATUS_NORMAL, WebSocketApp, \
    WebSocketConnectionClosedException
from .settings import Settings
from .utils import base64url_to_image, image_to_base64url


class ScalingMode(str, Enum):
    SHRINK = 'shrink'
    GROW = 'grow'


class ESRGANModel(str, Enum):
    # General
    GENERAL_X4_V3 = 'general_x4_v3'
    X4_PLUS = 'x4_plus'
    X2_PLUS = 'x2_plus'
    ESRNET_X4_PLUS = 'x4_plus'
    OFFICIAL_X4 = 'official_x4'

    # Anime/Illustrations
    X4_PLUS_ANIME_6B = 'x4_plus_anime_6b'

    # Anime video
    ANIME_VIDEO_V3 = 'anime_video_v3'


class GFPGANModel(str, Enum):
    V1_3 = 'V1.3'
    V1_2 = 'V1.2'
    V1 = 'V1'


class WebSocketException(Exception):
    def __init__(self, message):
        self.message = message


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

    def _websocket_request(
            self,
            request: str,
            request_data: Dict[str, Any],
            progress_callback: Optional[Callable[[float], None]] = None,
    ) -> Dict[str, Any]:
        response: Optional[Dict[str, Any]] = None

        def on_error(_, error):
            if isinstance(error, WebSocketConnectionClosedException):
                error = WebSocketException(
                    'Connection to server closed unexpectedly. See server logs for details'
                )
            if isinstance(error, ConnectionRefusedError):
                error = WebSocketException('Couldn\'t connect to server')
            raise error

        def on_close(_, status_code: int, message: str):
            if status_code != STATUS_NORMAL:
                raise WebSocketException(message)
            if not response or response.get('status') != self.WebSocketResponseStatus.FINISHED:
                raise WebSocketException('Haven\'t received ')

        def on_message(ws: WebSocketApp, message: str):
            try:
                nonlocal response
                response = json.loads(message)
                if 'status' not in response:
                    raise WebSocketException(f'Wrong response format:\n{message}')

                if response['status'] == self.WebSocketResponseStatus.PROGRESS:
                    progress_callback(response['progress'])
            except JSONDecodeError:
                raise WebSocketException(
                    f'Client received message that is not in json format:\n{message}'
                )

        def on_open(ws: WebSocketApp):
            ws.send(json.dumps({'username': self._auth[0], 'password': self._auth[1]}))
            ws.send(json.dumps(request_data))

        app = WebSocketApp(
            self._base_websocket_url + request,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
        )
        app.run_forever()

        return response

    def do_diffusion_request(
            self,
            request: str,
            prompt: str,
            num_variants: int = 6,
            num_inference_steps: int = 50,
            guidance_scale: float = 7.5,
            seed: Optional[int] = None,
            progress_callback: Optional[Callable[[float], None]] = None,
            scaling_mode: ScalingMode = ScalingMode.GROW,
            **kwargs
    ):
        request_data = {
            'prompt': prompt,
            'num_inference_steps': num_inference_steps,
            'guidance_scale': guidance_scale,
            'num_variants': num_variants,
            'output_format': 'PNG',
            'scaling_mode': scaling_mode,
        }
        request_data.update(kwargs)
        if seed is not None:
            request_data['seed'] = seed

        response = self._websocket_request(request, request_data, progress_callback)

        images = response['result']['images']
        return [base64url_to_image(image.encode()) for image in images]

    def text_to_image(
            self,
            prompt: str,
            aspect_ratio: float,
            num_variants: int = 6,
            num_inference_steps: int = 50,
            guidance_scale: float = 7.5,
            seed: Optional[int] = None,
            progress_callback: Optional[Callable[[float], None]] = None,
            scaling_mode: ScalingMode = ScalingMode.GROW
    ) -> List[Image.Image]:
        return self.do_diffusion_request(
            'text_to_image',
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            num_variants=num_variants,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            seed=seed,
            progress_callback=progress_callback,
            scaling_mode=scaling_mode
        )

    def image_to_image(
            self,
            prompt: str,
            source_image: Image.Image,
            strength: float = 0.8,
            num_variants: int = 6,
            num_inference_steps: int = 50,
            guidance_scale: float = 7.5,
            seed: Optional[int] = None,
            progress_callback: Optional[Callable[[float], None]] = None,
            scaling_mode: ScalingMode = ScalingMode.GROW
    ) -> List[Image.Image]:
        return self.do_diffusion_request(
            'image_to_image',
            prompt=prompt,
            source_image=image_to_base64url(source_image).decode(),
            strength=strength,
            num_variants=num_variants,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            seed=seed,
            progress_callback=progress_callback,
            scaling_mode=scaling_mode
        )

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
            progress_callback: Optional[Callable[[float], None]] = None,
            scaling_mode: ScalingMode = ScalingMode.GROW
    ) -> List[Image.Image]:
        extra_kwargs = {}
        if mask is not None:
            extra_kwargs['mask'] = image_to_base64url(mask).decode()
        return self.do_diffusion_request(
            'inpainting',
            prompt=prompt,
            source_image=image_to_base64url(source_image).decode(),
            strength=strength,
            num_variants=num_variants,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            seed=seed,
            progress_callback=progress_callback,
            scaling_mode=scaling_mode,
            **extra_kwargs
        )

    def gobig(
            self,
            prompt: str,
            source_image: Image.Image,
            target_width: int,
            target_height: int,
            use_real_esrgan: bool = True,
            esrgan_model: ESRGANModel = ESRGANModel.GENERAL_X4_V3,
            maximize: bool = True,
            overlap: int = 64,
            strength: float = 0.8,
            num_inference_steps: int = 50,
            guidance_scale: float = 7.5,
            seed: Optional[int] = None,
            progress_callback: Optional[Callable[[float], None]] = None,
    ) -> Image.Image:
        request_data = {
            'prompt': prompt,
            'output_format': 'PNG',
            'num_inference_steps': num_inference_steps,
            'guidance_scale': guidance_scale,
            'seed': seed,
            'image': image_to_base64url(source_image).decode(),
            'use_real_esrgan': use_real_esrgan,
            'esrgan_model': esrgan_model,
            'maximize': maximize,
            'strength': strength,
            'target_width': target_width,
            'target_height': target_height,
            'overlap': overlap
        }
        response = self._websocket_request('gobig', request_data, progress_callback)
        return base64url_to_image(response['result']['image'].encode())

    def upscale(
            self,
            source_image: Image.Image,
            target_width: int,
            target_height: int,
            esrgan_model: ESRGANModel = ESRGANModel.GENERAL_X4_V3,
            maximize: bool = True
    ) -> Image.Image:
        request_data = {
            'image': image_to_base64url(source_image).decode(),
            'target_width': target_width,
            'target_height': target_height,
            'model': esrgan_model,
            'maximize': maximize
        }

        response = httpx.post(
            self._base_http_url + 'upscale',
            json=request_data,
            headers=self._default_headers,
            timeout=None,
            auth=self._auth
        )
        response.raise_for_status()
        return base64url_to_image(response.json()['image'].encode())

    def restore_face(
            self,
            source_image: Image.Image,
            model_type: GFPGANModel = GFPGANModel.V1_3,
            use_real_esrgan: bool = True,
            bg_tile: int = 400,
            upscale: int = 2,
            aligned: bool = False,
            only_center_face: bool = False
    ) -> Image.Image:
        request_data = {
            'image': image_to_base64url(source_image).decode(),
            'model_type': model_type,
            'use_real_esrgan': use_real_esrgan,
            'bg_tile': bg_tile,
            'upscale': upscale,
            'aligned': aligned,
            'only_center_face': only_center_face
        }

        response = httpx.post(
            self._base_http_url + 'restore_face',
            json=request_data,
            headers=self._default_headers,
            timeout=None,
            auth=self._auth
        )
        response.raise_for_status()
        return base64url_to_image(response.json()['image'].encode())

    def test_connection(self) -> Tuple[bool, str]:
        try:
            response = httpx.get(
                self._base_http_url + 'ping', headers=self._default_headers, auth=self._auth
            )
            response.status_code == httpx.codes.OK, response.text
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

    @classmethod
    def refresh_credentials(cls):
        if cls.client() is not None:
            cls.client()._auth = (Settings.settings().USERNAME, Settings.settings().PASSWORD)
