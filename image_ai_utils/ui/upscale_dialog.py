from enum import Enum
from typing import Optional

from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog

from PIL import Image
from PIL.ImageQt import ImageQt
from .utils import get_ui_file_path
from ..client import diffusion_client


class UpscaleDialog(QDialog):
    class UpscalingMode(str, Enum):
        GOBIG = 'gobig'
        REAL_ESRGAN = 'real_esrgan'

    def __init__(self):
        super().__init__()
        uic.loadUi(get_ui_file_path('upscale_dialog.ui'), self)

        self._upscaling_mode = self.UpscalingMode.REAL_ESRGAN
        self._source_image: Optional[Image.Image] = None
        self._result_image: Optional[Image.Image] = None

    def set_upscaling_params(
            self, source_image: Image.Image, target_width: int, target_height: int
    ):
        self._source_image = source_image
        self.target_width_spin_box.setValue(target_width)
        self.target_height_spin_box.setValue(target_height)

        self._imageqt = ImageQt(self._source_image)
        pixmap = QPixmap.fromImage(self._imageqt)
        self.image_label.setPixmap(pixmap)

        self.apply_button.setEnabled(True)

    def upscale(self):
        self._result_image = diffusion_client.upscale(
            source_image=self._source_image,
            target_width=self.target_width_spin_box.value(),
            target_height=self.target_height_spin_box.value(),
        )

        self._imageqt = ImageQt(self._result_image)
        pixmap = QPixmap.fromImage(self._imageqt)
        self.image_label.setPixmap(pixmap)

        self.apply_button.setEnabled(True)

    @property
    def result_image(self) -> Optional[Image.Image]:
        return self._result_image

    def apply(self):
        self.accept()
