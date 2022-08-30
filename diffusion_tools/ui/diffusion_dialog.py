from enum import Enum
from typing import Optional

from PyQt5 import uic
from PyQt5.QtCore import QRect
from PyQt5.QtGui import QPixmap, QPainter, QPaintEvent
from PyQt5.QtWidgets import QDialog, QPushButton, QSizePolicy

from PIL import Image
from PIL.ImageQt import ImageQt
from .upscale_dialog import UpscaleDialog
from .utils import get_ui_file_path
from ..client import diffusion_client


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


class DiffusionDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(get_ui_file_path('diffusion_dialog.ui'), self)
        self.use_random_seed_check_box.stateChanged.connect(
            lambda state: self.seed_spin_box.setEnabled(not state)
        )
        self.upscale_dialog = UpscaleDialog()
        self._columns = 2  # TODO change dynamically
        self._source_images = []
        self._result_images = []
        self._image_selection = []
        self._target_width = 512
        self._target_height = 512
        self._mode: Optional[DiffusionMode] = None
        self._source_image: Optional[Image.Image] = None
        self._imageqt = None

    def set_source_image(self, source_image: Image.Image):
        self._source_image = source_image

    def upscale(self):
        if not self.upscale_dialog.exec():
            return

    def apply(self):
        self.accept()

    def generate(self):
        # TODO separate widget
        request_data = {
            'prompt': self.prompt_plain_text_edit.toPlainText(),
            'num_inference_steps': self.inference_spin_box.value(),
            'guidance_scale': self.guidance_scale_double_spin_box.value(),
            'num_variants': self.number_of_variants_spin_box.value()
        }
        if not self.use_random_seed_check_box.isChecked:
            request_data['seed'] = self.seed_spin_box.value()

        if self._mode == DiffusionMode.TEXT_TO_IMAGE:
            aspect_ratio = self._target_width / self._target_height
            request_data['aspect_ratio'] = aspect_ratio
            # TODO async or separate thread
            self._result_images = diffusion_client.text_to_image(**request_data)
        elif self._mode == DiffusionMode.IMAGE_TO_IMAGE:
            request_data['strength'] = self.strength_double_spin_box.value()
            request_data['source_image'] = self._source_image
            self._result_images = diffusion_client.image_to_image(**request_data)
        else:
            return

        # Data gets corrupted if we do it in one go or don't save
        self._imageqt = [ImageQt(image) for image in self._result_images]
        pixmaps = [QPixmap.fromImage(image) for image in self._imageqt]

        layout = self.images_grid_layout
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            layout.removeItem(item)
            current_widget = item.widget()
            if current_widget:
                current_widget.setParent(None)

        self._image_selection = [False] * len(self._result_images)
        self.upscale_selected_button.setEnabled(False)
        self.apply_button.setEnabled(False)
        for i, pixmap in enumerate(pixmaps):
            button = ImageSelectButton(pixmap)
            button.toggled.connect(self._get_toggle_image_slot(i))
            layout.addWidget(button, i // self._columns, i % self._columns)

    def _get_toggle_image_slot(self, i: int):
        def _toggle(checked: bool):
            self._image_selection[i] = checked
            any_selected = any(self._image_selection)
            self.upscale_selected_button.setEnabled(any_selected)
            self.apply_button.setEnabled(any_selected)

        return _toggle

    def set_mode(self, mode: DiffusionMode):
        self._mode = mode
        self.strength_label.setVisible(mode != DiffusionMode.TEXT_TO_IMAGE)
        self.strength_double_spin_box.setVisible(mode != DiffusionMode.TEXT_TO_IMAGE)

    def set_target_size(self, width, height):
        self._target_width = width
        self._target_height = height

    @property
    def result_images(self):
        return [
            image for selected, image in zip(self._image_selection, self._result_images) if selected
        ]
