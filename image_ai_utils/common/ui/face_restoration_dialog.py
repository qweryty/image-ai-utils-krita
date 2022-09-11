from typing import Optional

from PIL import Image

from httpx import HTTPStatusError

import httpx
from PyQt5.QtGui import QPixmap

from PIL.ImageQt import ImageQt
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QComboBox, QSpinBox, QCheckBox, QPushButton, QLabel

from .exception_dialog import ExceptionDialog
from ..client import ImageAIUtilsClient, GFPGANModel
from ..utils import get_ui_file_path

GFPGAN_MODELS = [GFPGANModel.V1_3, GFPGANModel.V1_2, GFPGANModel.V1]


class FaceRestorationDialog(QDialog):
    model_combo_box: QComboBox
    use_real_esrgan_check_box: QCheckBox
    background_tile_spin_box: QSpinBox
    upscale_factor_spin_box: QSpinBox
    only_center_face_check_box: QCheckBox
    apply_button: QPushButton
    image_label: QLabel

    def __init__(self):
        super().__init__()
        uic.loadUi(get_ui_file_path('face_restoration_dialog.ui'), self)

        self._source_image: Optional[Image.Image] = None
        self._result_image: Optional[Image.Image] = None
        self.apply_button.setEnabled(False)

    def set_source_image(self, source_image: Image.Image):
        self._source_image = source_image
        self._imageqt = ImageQt(self._source_image)
        pixmap = QPixmap.fromImage(self._imageqt)
        self.image_label.setPixmap(pixmap)
        self.apply_button.setEnabled(False)

    def restore_face(self):
        try:
            self._result_image = ImageAIUtilsClient.client().restore_face(
                source_image=self._source_image,
                model_type=GFPGAN_MODELS[self.model_combo_box.currentIndex()],
                use_real_esrgan=self.use_real_esrgan_check_box.isChecked(),
                bg_tile=self.background_tile_spin_box.value(),
                upscale=self.upscale_factor_spin_box.value(),
                only_center_face=self.only_center_face_check_box.isChecked()
            )
        except HTTPStatusError as e:
            ExceptionDialog(f'{e.response.status_code}: {e.response.text}').exec()
            return
        except httpx.ConnectError:
            ExceptionDialog(f'Could not connect to server').exec()
            return

        self._imageqt = ImageQt(self._result_image)
        pixmap = QPixmap.fromImage(self._imageqt)
        self.image_label.setPixmap(pixmap)
        self.apply_button.setEnabled(True)

    @property
    def result_image(self) -> Optional[Image.Image]:
        return self._result_image

    def apply(self):
        self.accept()
