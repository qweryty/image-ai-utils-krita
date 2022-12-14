from enum import Enum
from typing import Optional, List

from PyQt5 import uic
from PyQt5.QtCore import QRect
from PyQt5.QtGui import QPixmap, QPainter, QPaintEvent
from PyQt5.QtWidgets import QDialog, QPushButton, QSizePolicy, QCheckBox, QSpinBox, QGridLayout, \
    QTextEdit, QDoubleSpinBox, QLabel, QComboBox

from PIL import Image
from PIL.ImageQt import ImageQt
from .exception_dialog import ExceptionDialog
from .progress_bar_dialog import ProgressBarDialog
from .upscale_dialog import UpscaleDialog
from ..client import ImageAIUtilsClient
from ..progress_thread import ProgressThread
from ..utils import get_ui_file_path


class ImageSelectButton(QPushButton):
    def __init__(self, pixmap: QPixmap, label=None, parent=None):
        super().__init__(label, parent)

        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._pixmap = pixmap
        self._margin = 5
        self._aspect_ratio = self._pixmap.width() / self._pixmap.height()
        self.setStyleSheet('QPushButton:checked { border: 3px solid blue }"')

    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        painter = QPainter()
        painter.begin(self)

        button_rectangle = self.rect()
        height = button_rectangle.height() - self._margin * 2
        width = button_rectangle.width() - self._margin * 2
        image_rectangle = QRect(0, 0, width, height)
        image_rectangle.moveCenter(button_rectangle.center())
        painter.drawPixmap(image_rectangle, self._pixmap)

        painter.end()

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width):
        return int(width / self._aspect_ratio)


class DiffusionMode(int, Enum):
    TEXT_TO_IMAGE = 0
    IMAGE_TO_IMAGE = 1
    INPAINT = 2
    MAKE_TILABLE = 3


class DiffusionDialog(QDialog):
    use_random_seed_check_box: QCheckBox
    seed_spin_box: QSpinBox
    upscale_selected_button: QPushButton
    apply_button: QPushButton
    images_grid_layout: QGridLayout
    prompt_plain_text_edit: QTextEdit
    inference_spin_box: QSpinBox
    guidance_scale_double_spin_box: QSpinBox
    strength_label: QLabel
    strength_double_spin_box: QDoubleSpinBox
    number_of_variants_spin_box: QSpinBox
    scaling_mode_combo_box: QComboBox
    border_width_label: QLabel
    border_width_spin_box: QSpinBox
    border_softness_label: QLabel
    border_softness_double_spin_box: QDoubleSpinBox

    def __init__(self):
        super().__init__()
        uic.loadUi(get_ui_file_path('diffusion_dialog.ui'), self)
        self.use_random_seed_check_box.stateChanged.connect(
            lambda state: self.seed_spin_box.setEnabled(not state)
        )
        self.upscale_dialog = UpscaleDialog()
        self.progress_bar_dialog = ProgressBarDialog()
        self._columns = 2  # TODO change dynamically
        self._result_images: List[Image.Image] = []
        self._result_mask: Optional[Image.Image] = None
        self._image_selection = []
        self._target_width = 512
        self._target_height = 512
        self._mode: Optional[DiffusionMode] = None
        self._source_image: Optional[Image.Image] = None
        self._mask: Optional[Image.Image] = None
        self._imageqt = None

    def set_source_image(self, source_image: Image.Image):
        self._source_image = source_image

    def set_mask(self, mask: Optional[Image.Image]):
        self._mask = mask

    def _update_buttons(self):
        layout = self.images_grid_layout
        # Removing old buttons
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            layout.removeItem(item)
            current_widget = item.widget()
            if current_widget:
                current_widget.setParent(None)

        # Data gets corrupted if we do it in one go or don't save
        self._imageqt = [ImageQt(image) for image in self._result_images]
        pixmaps = [QPixmap.fromImage(image) for image in self._imageqt]

        self._image_selection = [False] * len(self._result_images)
        self.upscale_selected_button.setEnabled(False)
        self.apply_button.setEnabled(False)
        for i, pixmap in enumerate(pixmaps):
            button = ImageSelectButton(pixmap)
            button.toggled.connect(self._get_toggle_image_slot(i))
            layout.addWidget(button, i // self._columns, i % self._columns)

    def upscale(self):
        selected_id = self._image_selection.index(True)
        self.upscale_dialog.set_upscaling_params(
            source_image=self._result_images[selected_id],
            target_width=self._target_width,
            target_height=self._target_height,
            prompt=self.prompt_plain_text_edit.toPlainText()
        )
        if not self.upscale_dialog.exec():
            return

        self._result_images[selected_id] = self.upscale_dialog.result_image
        self._update_buttons()

    def apply(self):
        self.accept()

    def generate(self):
        # TODO separate widget
        request_data = {
            'prompt': self.prompt_plain_text_edit.toPlainText(),
            'num_inference_steps': self.inference_spin_box.value(),
            'guidance_scale': self.guidance_scale_double_spin_box.value(),
            'num_variants': self.number_of_variants_spin_box.value(),
            'scaling_mode': self.scaling_mode_combo_box.currentText()
        }
        if not self.use_random_seed_check_box.isChecked():
            request_data['seed'] = self.seed_spin_box.value()

        if self._mode == DiffusionMode.TEXT_TO_IMAGE:
            aspect_ratio = self._target_width / self._target_height
            request_data['aspect_ratio'] = aspect_ratio
            thread = ProgressThread(ImageAIUtilsClient.client().text_to_image, request_data)
        elif self._mode == DiffusionMode.IMAGE_TO_IMAGE:
            request_data['strength'] = self.strength_double_spin_box.value()
            request_data['source_image'] = self._source_image
            thread = ProgressThread(ImageAIUtilsClient.client().image_to_image, request_data)
        elif self._mode == DiffusionMode.INPAINT:
            request_data['strength'] = self.strength_double_spin_box.value()
            request_data['source_image'] = self._source_image
            request_data['mask'] = self._mask
            thread = ProgressThread(ImageAIUtilsClient.client().inpaint, request_data)
        elif self._mode == DiffusionMode.MAKE_TILABLE:
            request_data['strength'] = self.strength_double_spin_box.value()
            request_data['source_image'] = self._source_image
            request_data['border_width'] = self.border_width_spin_box.value()
            request_data['border_softness'] = self.border_softness_double_spin_box.value()
            thread = ProgressThread(ImageAIUtilsClient.client().make_tilable, request_data)
        else:
            return

        self.progress_bar_dialog.set_progress(0)
        thread.progress_signal.connect(self.progress_bar_dialog.set_progress)
        thread.finished.connect(self.progress_bar_dialog.accept)
        thread.start()
        self.progress_bar_dialog.exec()
        thread.wait()
        if not thread.success:
            ExceptionDialog(thread.error_message).exec()
            return

        if self._mode == DiffusionMode.MAKE_TILABLE:
            self._result_images, self._result_mask = thread.result
        else:
            self._result_images = thread.result

        self._update_buttons()

    def _get_toggle_image_slot(self, i: int):
        def _toggle(checked: bool):
            self._image_selection[i] = checked
            self.upscale_selected_button.setEnabled(sum(self._image_selection) == 1)
            self.apply_button.setEnabled(any(self._image_selection))

        return _toggle

    def set_mode(self, mode: DiffusionMode):
        self._mode = mode
        self.strength_label.setVisible(mode != DiffusionMode.TEXT_TO_IMAGE)
        self.strength_double_spin_box.setVisible(mode != DiffusionMode.TEXT_TO_IMAGE)
        self.border_width_label.setVisible(mode == DiffusionMode.MAKE_TILABLE)
        self.border_width_spin_box.setVisible(mode == DiffusionMode.MAKE_TILABLE)
        self.border_softness_label.setVisible(mode == DiffusionMode.MAKE_TILABLE)
        self.border_softness_double_spin_box.setVisible(mode == DiffusionMode.MAKE_TILABLE)

    def set_target_size(self, width, height):
        self._target_width = width
        self._target_height = height

    @property
    def result_images(self) -> List[Image.Image]:
        return [
            image for selected, image in zip(self._image_selection, self._result_images) if selected
        ]

    @property
    def result_mask(self) -> Optional[Image.Image]:
        return self._result_mask
