from enum import Enum
from typing import Optional, List

from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QSpinBox, QLabel, QPushButton, QWidget, QCheckBox, \
    QDoubleSpinBox, QComboBox, QPlainTextEdit

from PIL import Image
from PIL.ImageQt import ImageQt
from .exception_dialog import ExceptionDialog
from .progress_bar_dialog import ProgressBarDialog
from ..progress_thread import ProgressThread
from ..utils import get_ui_file_path
from ..client import ImageAIUtilsClient, ESRGANModel

ESRGAN_MODELS = [
    ESRGANModel.GENERAL_X4_V3,
    ESRGANModel.X4_PLUS,
    ESRGANModel.X2_PLUS,
    ESRGANModel.ESRNET_X4_PLUS,
    ESRGANModel.OFFICIAL_X4,
    ESRGANModel.X4_PLUS_ANIME_6B,
    ESRGANModel.ANIME_VIDEO_V3
]


class UpscaleDialog(QDialog):
    target_width_spin_box: QSpinBox
    target_height_spin_box: QSpinBox
    image_label: QLabel
    apply_button: QPushButton
    use_realesrgan_check_box: QCheckBox
    use_realesrgan_label: QLabel
    init_strength_double_spin_box: QDoubleSpinBox
    init_strength_label: QLabel
    upscale_mode_combo_box: QComboBox
    esrgan_model_combo_box: QComboBox
    maximize_check_box: QCheckBox
    gobig_overlap_spin_box: QSpinBox
    gobig_overlap_label: QLabel
    original_width_label: QLabel
    original_height_label: QLabel
    lock_aspect_ratio_check_box: QCheckBox
    width_scale_label: QLabel
    width_scale_spin_box: QDoubleSpinBox
    height_scale_label: QLabel
    height_scale_spin_box: QDoubleSpinBox
    scale_label: QLabel
    scale_spin_box: QDoubleSpinBox
    prompt_plain_text_edit: QPlainTextEdit
    prompt_label: QLabel
    inference_steps_spin_box: QSpinBox
    inference_steps_label: QLabel
    use_random_seed_check_box: QCheckBox
    use_random_seed_label: QLabel
    seed_spin_box: QSpinBox
    seed_label: QLabel
    guidance_scale_double_spin_box: QDoubleSpinBox
    guidance_scale_label: QLabel

    class UpscalingMode(int, Enum):
        REAL_ESRGAN = 0
        GOBIG = 1

    def __init__(self):
        super().__init__()
        uic.loadUi(get_ui_file_path('upscale_dialog.ui'), self)

        self.use_random_seed_check_box.stateChanged.connect(
            lambda state: self.seed_spin_box.setEnabled(not state)
        )
        self.progress_bar_dialog = ProgressBarDialog()
        self._upscaling_mode = self.UpscalingMode.REAL_ESRGAN
        self._source_image: Optional[Image.Image] = None
        self._result_image: Optional[Image.Image] = None
        self._require_gobig: List[QWidget] = [
            self.use_realesrgan_check_box,
            self.use_realesrgan_label,
            self.init_strength_double_spin_box,
            self.init_strength_label,
            self.gobig_overlap_spin_box,
            self.gobig_overlap_label,
            self.prompt_plain_text_edit,
            self.prompt_label,
            self.inference_steps_spin_box,
            self.inference_steps_label,
            self.use_random_seed_check_box,
            self.use_random_seed_label,
            self.seed_spin_box,
            self.seed_label,
            self.guidance_scale_double_spin_box,
            self.guidance_scale_label
        ]

        self.change_mode(self.upscale_mode_combo_box.currentIndex())
        self.toggle_lock_aspect_ratio(self.lock_aspect_ratio_check_box.isChecked())

    def change_mode(self, mode: int):
        self._upscaling_mode = mode
        if self._upscaling_mode != self.UpscalingMode.GOBIG:
            for widget in self._require_gobig:
                widget.setVisible(False)
        else:
            for widget in self._require_gobig:
                widget.setVisible(True)

    def update_target_width(self, width: int):
        if self.lock_aspect_ratio_check_box.isChecked():
            self.scale_spin_box.blockSignals(True)
            self.scale_spin_box.setValue(width / self._source_image.width)
            self.scale_spin_box.blockSignals(False)
        else:
            self.width_scale_spin_box.blockSignals(True)
            self.width_scale_spin_box.setValue(width / self._source_image.width)
            self.width_scale_spin_box.blockSignals(False)

    def update_target_height(self, height: int):
        if self.lock_aspect_ratio_check_box.isChecked():
            self.scale_spin_box.blockSignals(True)
            self.scale_spin_box.setValue(height / self._source_image.height)
            self.scale_spin_box.blockSignals(False)
        else:
            self.height_scale_spin_box.blockSignals(True)
            self.height_scale_spin_box.setValue(height / self._source_image.height)
            self.height_scale_spin_box.blockSignals(False)

    def update_width_scale(self, width_scale: float):
        self.target_width_spin_box.blockSignals(True)
        self.target_width_spin_box.setValue(int(self._source_image.width * width_scale))
        self.target_width_spin_box.blockSignals(False)

    def update_height_scale(self, height_scale: float):
        self.target_height_spin_box.blockSignals(True)
        self.target_height_spin_box.setValue(int(self._source_image.height * height_scale))
        self.target_height_spin_box.blockSignals(False)

    def update_scale(self, scale: float):
        self.target_width_spin_box.blockSignals(True)
        self.target_height_spin_box.blockSignals(True)
        self.target_width_spin_box.setValue(int(self._source_image.width * scale))
        self.target_height_spin_box.setValue(int(self._source_image.height * scale))
        self.target_width_spin_box.blockSignals(False)
        self.target_height_spin_box.blockSignals(False)

    def toggle_lock_aspect_ratio(self, aspect_ratio_locked: bool):
        self.width_scale_spin_box.setVisible(not aspect_ratio_locked)
        self.width_scale_label.setVisible(not aspect_ratio_locked)
        self.height_scale_spin_box.setVisible(not aspect_ratio_locked)
        self.height_scale_label.setVisible(not aspect_ratio_locked)
        self.scale_spin_box.setVisible(aspect_ratio_locked)
        self.scale_label.setVisible(aspect_ratio_locked)

        if aspect_ratio_locked:
            self.scale_spin_box.setValue(self.width_scale_spin_box.value())
        else:
            self.width_scale_spin_box.setValue(self.scale_spin_box.value())
            self.height_scale_spin_box.setValue(self.scale_spin_box.value())

    def set_upscaling_params(
            self, source_image: Image.Image, target_width: int, target_height: int, prompt: str
    ):
        self.lock_aspect_ratio_check_box.setChecked(False)
        self.prompt_plain_text_edit.setPlainText(prompt)
        self._source_image = source_image
        source_width, source_height = self._source_image.size
        self.original_width_label.setText(str(source_width))
        self.original_height_label.setText(str(source_height))
        self.target_width_spin_box.setValue(target_width)
        self.target_height_spin_box.setValue(target_height)

        self._imageqt = ImageQt(self._source_image)
        pixmap = QPixmap.fromImage(self._imageqt)
        self.image_label.setPixmap(pixmap)

        self.apply_button.setEnabled(False)

    def upscale(self):
        if self.upscale_mode_combo_box.currentIndex() == self.UpscalingMode.REAL_ESRGAN:
            self._result_image = ImageAIUtilsClient.client().upscale(
                source_image=self._source_image,
                target_width=self.target_width_spin_box.value(),
                target_height=self.target_height_spin_box.value(),
                esrgan_model=ESRGAN_MODELS[self.esrgan_model_combo_box.currentIndex()]
            )

        else:
            request_data = {
                'prompt': self.prompt_plain_text_edit.toPlainText(),
                'source_image': self._source_image,
                'target_width': self.target_width_spin_box.value(),
                'target_height': self.target_height_spin_box.value(),
                'use_real_esrgan': self.use_realesrgan_check_box.isChecked(),
                'esrgan_model': ESRGAN_MODELS[self.esrgan_model_combo_box.currentIndex()],
                'maximize': self.maximize_check_box.isChecked(),
                'overlap': self.gobig_overlap_spin_box.value(),
                'strength': self.init_strength_double_spin_box.value(),
                'num_inference_steps': self.inference_steps_spin_box.value(),
                'guidance_scale': self.guidance_scale_double_spin_box.value(),
            }

            if not self.use_random_seed_check_box.isChecked():
                request_data['seed'] = self.seed_spin_box.value()

            thread = ProgressThread(ImageAIUtilsClient.client().gobig, request_data)
            self.progress_bar_dialog.set_progress(0)
            thread.progress_signal.connect(self.progress_bar_dialog.set_progress)
            thread.finished.connect(self.progress_bar_dialog.accept)
            thread.start()
            self.progress_bar_dialog.exec()
            thread.wait()
            if not thread.success:
                ExceptionDialog(thread.error_message).exec()
                return

            self._result_image = thread.result

        self._imageqt = ImageQt(self._result_image)
        pixmap = QPixmap.fromImage(self._imageqt)
        self.image_label.setPixmap(pixmap)
        self.apply_button.setEnabled(True)

    @property
    def result_image(self) -> Optional[Image.Image]:
        return self._result_image

    def apply(self):
        self.accept()
