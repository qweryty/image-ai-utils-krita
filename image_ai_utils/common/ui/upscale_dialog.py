from enum import Enum
from typing import Optional, List

from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QSpinBox, QLabel, QPushButton, QWidget, QCheckBox, \
    QDoubleSpinBox, QComboBox

from PIL import Image
from PIL.ImageQt import ImageQt
from ..utils import get_ui_file_path
from ..client import ImageAIUtilsClient


class UpscaleDialog(QDialog):
    target_width_spin_box: QSpinBox
    target_height_spin_box: QSpinBox
    image_label: QLabel
    apply_button: QPushButton
    use_realesrgan_check_box: QCheckBox
    init_strength_double_spin_box: QDoubleSpinBox
    upscale_mode_combo_box: QComboBox
    use_realesrgan_label: QLabel
    init_strength_label: QLabel

    class UpscalingMode(int, Enum):
        REAL_ESRGAN = 0
        GOBIG = 1

    def __init__(self):
        super().__init__()
        uic.loadUi(get_ui_file_path('upscale_dialog.ui'), self)

        self._upscaling_mode = self.UpscalingMode.REAL_ESRGAN
        self._source_image: Optional[Image.Image] = None
        self._result_image: Optional[Image.Image] = None
        self._require_gobig: List[QWidget] = [
            self.use_realesrgan_check_box,
            self.init_strength_double_spin_box,
            self.use_realesrgan_label,
            self.init_strength_label
        ]

        self.change_mode(self.upscale_mode_combo_box.currentIndex())

    def change_mode(self, mode: int):
        self._upscaling_mode = mode
        if self._upscaling_mode != self.UpscalingMode.GOBIG:
            for widget in self._require_gobig:
                widget.setVisible(False)

    def set_upscaling_params(
            self, source_image: Image.Image, target_width: int, target_height: int
    ):
        self._source_image = source_image
        self.target_width_spin_box.setValue(target_width)
        self.target_height_spin_box.setValue(target_height)

        self._imageqt = ImageQt(self._source_image)
        pixmap = QPixmap.fromImage(self._imageqt)
        self.image_label.setPixmap(pixmap)

        self.apply_button.setEnabled(False)

    def upscale(self):
        self._result_image = ImageAIUtilsClient.client().upscale(
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
