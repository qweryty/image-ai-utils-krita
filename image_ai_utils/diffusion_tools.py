from enum import Enum
from typing import Optional, Tuple

from PyQt5 import uic
from PyQt5.QtWidgets import QMessageBox

from PIL import Image, ImageOps
from krita import Extension, DockWidget, Krita, Document, Node
from .common.settings import Settings
from .common.ui.diffusion_dialog import DiffusionMode, DiffusionDialog
from .common.ui.face_restoration_dialog import FaceRestorationDialog
from .common.ui.settings_dialog import SettingsDialog
from .common.ui.upscale_dialog import UpscaleDialog
from .common.utils import get_ui_file_path


class LayerType(str, Enum):
    PAINT_LAYER = 'paintlayer'
    GROUP_LAYER = 'grouplayer'
    FILE_LAYER = 'filelayer'
    FILTER_LAYER = 'filterlayer'
    FILL_LAYER = 'filllayer'
    CLONE_LAYER = 'clonelayer'
    VECTOR_LAYER = 'vectorlayer'
    TRANSPARENCY_MASK = 'transparencymask'
    FILTER_MASK = 'filtermask'
    TRANSFORM_MASK = 'transformmask'
    SELECTION_MASK = 'selectionmask'
    COLORIZE_MASK = 'colorizemask'


class NotEnoughInfoException(Exception):
    pass


class DiffusionToolsDockWidget(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Diffusion Tools')
        self.main_widget = uic.loadUi(get_ui_file_path('diffusion_tools_widget.ui'))

        self.main_widget.text_to_image_button.clicked.connect(self.text_to_image)
        self.main_widget.image_to_image_button.clicked.connect(self.image_to_image)
        self.main_widget.inpaint_button.clicked.connect(self.inpaint)
        self.main_widget.upscale_button.clicked.connect(self.upscale)
        self.main_widget.face_restoration_button.clicked.connect(self.face_restoration)
        self.main_widget.make_tilable_button.clicked.connect(self.make_tilable)
        self.main_widget.settings_button.clicked.connect(self.call_settings)

        self._depend_on_settings = [
            self.main_widget.text_to_image_button,
            self.main_widget.image_to_image_button,
            self.main_widget.inpaint_button,
        ]

        for widget in self._depend_on_settings:
            widget.setEnabled(Settings.settings() is not None)

        self.setWidget(self.main_widget)

        self.upscale_dialog = UpscaleDialog()
        self.diffusion_dialog = DiffusionDialog()
        self.settings_dialog = SettingsDialog()
        self.face_restoration_dialog = FaceRestorationDialog()

    def insert_layers_from_diffusion(self, below: bool = False):
        current_document = Krita.instance().activeDocument()
        x, y, width, height = self._get_document_selection(current_document)
        current_node = current_document.activeNode()
        parent = current_node.parentNode()

        if below:
            children = parent.childNodes()
            current_index = children.index(current_node) - 1
            if current_index >= 0:
                current_node = children[current_index]
            else:
                current_node = None

        for i, image in enumerate(self.diffusion_dialog.result_images):
            new_node = current_document.createNode(f'diffusion {i}', LayerType.PAINT_LAYER)
            pixel_bytes = image.convert('RGBA').resize((width, height)).tobytes('raw', 'BGRA')
            new_node.setPixelData(pixel_bytes, x, y, width, height)
            parent.addChildNode(new_node, current_node)

        current_document.refreshProjection()

    def _get_document_selection(self, document: Document) -> Tuple[int, int, int, int]:
        selection = document.selection()
        if selection is not None:
            return selection.x(), selection.y(), selection.width(), selection.height()
        else:
            return 0, 0, document.width(), document.height()

    def _get_current_info(
            self, check_layer_type: bool = True
    ) -> Tuple[Document, Tuple[int, int, int, int], Node, Image.Image]:
        current_document = Krita.instance().activeDocument()
        if not current_document:
            raise NotEnoughInfoException

        selection = self._get_document_selection(current_document)
        current_layer = current_document.activeNode()
        if check_layer_type and current_layer.type() != LayerType.PAINT_LAYER:
            raise NotEnoughInfoException

        image = self._image_from_layer(current_layer, *selection)
        return current_document, selection, current_layer, image

    def text_to_image(self):
        current_document = Krita.instance().activeDocument()
        if not current_document:
            return

        _, _, width, height = self._get_document_selection(current_document)
        self.diffusion_dialog.set_target_size(width, height)

        self.diffusion_dialog.set_mode(DiffusionMode.TEXT_TO_IMAGE)
        if not self.diffusion_dialog.exec():
            return

        self.insert_layers_from_diffusion()

    def _image_from_layer(
            self, layer: Node, x: int, y: int, width: int, height: int
    ) -> Optional[Image.Image]:
        pixel_bytes = layer.pixelData(x, y, width, height)  # BGRA pixels
        # TODO support other formats than rgba
        if layer.type() == LayerType.PAINT_LAYER:
            return Image.frombytes('RGBA', (width, height), pixel_bytes, 'raw', 'BGRA')
        if layer.type() == LayerType.TRANSPARENCY_MASK:
            return Image.frombytes('L', (width, height), pixel_bytes, 'raw')
        return None

    def image_to_image(self):
        try:
            current_document, (x, y, width, height), current_layer, image = self._get_current_info()
        except NotEnoughInfoException:
            return

        self.diffusion_dialog.set_target_size(width, height)
        self.diffusion_dialog.set_source_image(image)
        self.diffusion_dialog.set_mode(DiffusionMode.IMAGE_TO_IMAGE)
        if not self.diffusion_dialog.exec():
            return

        self.insert_layers_from_diffusion()

    def inpaint(self):
        try:
            current_document, (x, y, width, height), current_layer, image = self._get_current_info()
        except NotEnoughInfoException:
            return

        self.diffusion_dialog.set_target_size(width, height)
        self.diffusion_dialog.set_source_image(image)
        for layer in current_layer.childNodes():
            if layer.type() == LayerType.TRANSPARENCY_MASK:
                mask = layer
                break
        else:
            return

        mask_image = self._image_from_layer(mask, x, y, width, height)
        self.diffusion_dialog.set_mask(ImageOps.invert(mask_image))

        self.diffusion_dialog.set_mode(DiffusionMode.INPAINT)
        if not self.diffusion_dialog.exec():
            return

        self.insert_layers_from_diffusion(below=True)

    def upscale(self):
        try:
            current_document, (x, y, width, height), current_layer, image = self._get_current_info()
        except NotEnoughInfoException:
            return

        self.upscale_dialog.set_upscaling_params(
            source_image=image,
            target_width=width * 2,
            target_height=height * 2,
            lock_aspect_ratio=True
        )

        if not self.upscale_dialog.exec():
            return

        upscaled = self.upscale_dialog.result_image
        if current_document.selection() is None:
            current_document.setWidth(upscaled.width)
            current_document.setHeight(upscaled.height)

        parent = current_layer.parentNode()
        new_node = current_document.createNode(f'{current_layer.name()} upscaled', 'paintLayer')
        pixel_bytes = upscaled.convert('RGBA').tobytes('raw', 'BGRA')
        new_node.setPixelData(pixel_bytes, x, y, upscaled.width, upscaled.height)
        parent.addChildNode(new_node, current_layer)

    def face_restoration(self):
        try:
            current_document, (x, y, width, height), current_layer, image = self._get_current_info()
        except NotEnoughInfoException:
            return

        self.face_restoration_dialog.set_source_image(image)
        if not self.face_restoration_dialog.exec():
            return

        restored = self.face_restoration_dialog.result_image
        if current_document.selection() is None:
            current_document.setWidth(restored.width)
            current_document.setHeight(restored.height)

        parent = current_layer.parentNode()
        new_node = current_document.createNode(f'{current_layer.name()} restored', 'paintLayer')
        pixel_bytes = restored.convert('RGBA').tobytes('raw', 'BGRA')
        new_node.setPixelData(pixel_bytes, x, y, restored.width, restored.height)
        parent.addChildNode(new_node, current_layer)

    def make_tilable(self):
        try:
            current_document, (x, y, width, height), current_layer, image = self._get_current_info()
        except NotEnoughInfoException:
            return

        self.diffusion_dialog.set_target_size(width, height)
        self.diffusion_dialog.set_source_image(image)
        self.diffusion_dialog.set_mode(DiffusionMode.MAKE_TILABLE)
        if not self.diffusion_dialog.exec():
            return

        # FIXME seems to be bug in krita, addChildNode produces invalid mask
        '''mask_node = current_document.createNode('mask', LayerType.TRANSPARENCY_MASK)
        print(self.diffusion_dialog.result_mask.mode)
        self.diffusion_dialog.result_mask.save('../out/mask.png')
        pixel_bytes = self.diffusion_dialog.result_mask.convert('L').resize(
            (width, height)
        ).tobytes('raw')
        print(len(pixel_bytes))
        mask_node.setPixelData(pixel_bytes, x, y, width, height)
        current_layer.addChildNode(mask_node, None)'''

        self.insert_layers_from_diffusion()

    def call_settings(self):
        self.settings_dialog.init_fields()
        if not self.settings_dialog.exec():
            return

        for widget in self._depend_on_settings:
            widget.setEnabled(True)

    def canvasChanged(self, canvas: 'Canvas') -> None:
        pass


class DiffusionToolsExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def system_check(self):
        # QMessageBox creates quick popup with information
        messageBox = QMessageBox()
        messageBox.setInformativeText(Application.version())
        messageBox.setWindowTitle('System Check')
        messageBox.setText('Hello! Here is the version of Krita you are using.')
        messageBox.setStandardButtons(QMessageBox.Close)
        messageBox.setIcon(QMessageBox.Information)
        messageBox.exec()

    def createActions(self, window):
        action = window.createAction("", "System Check")
        action.triggered.connect(self.system_check)
        pass
