import io

from PIL import Image, ImageOps
from PyQt5 import uic
from PyQt5.QtWidgets import QMessageBox

from krita import Extension, DockWidget, Krita, Document, Node
from .ui.diffusion_dialog import DiffusionMode, DiffusionDialog
from .ui.upscale_dialog import UpscaleDialog
from .ui.utils import get_ui_file_path


class DiffusionToolsDockWidget(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Diffusion Tools')
        self.main_widget = uic.loadUi(get_ui_file_path('diffusion_tools_widget.ui'))

        self.main_widget.text_to_image_button.clicked.connect(self.text_to_image)
        self.main_widget.image_to_image_button.clicked.connect(self.image_to_image)
        self.main_widget.inpaint_button.clicked.connect(self.inpaint)
        self.main_widget.upscale_button.clicked.connect(self.upscale)

        self.setWidget(self.main_widget)

        self.upscale_dialog = UpscaleDialog()
        self.diffusion_dialog = DiffusionDialog()

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
            new_node = current_document.createNode(f'diffusion {i}', 'paintLayer')
            pixel_bytes = image.convert('RGBA').resize((width, height)).tobytes('raw', 'BGRA')
            new_node.setPixelData(pixel_bytes, x, y, width, height)
            parent.addChildNode(new_node, current_node)

        current_document.refreshProjection()

    def _get_document_selection(self, document: Document):
        selection = document.selection()
        if selection is not None:
            return selection.x(), selection.y(), selection.width(), selection.height()
        else:
            return 0, 0, document.width(), document.height()

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

    def image_to_image(self):
        current_document = Krita.instance().activeDocument()
        if not current_document:
            return

        x, y, width, height = self._get_document_selection(current_document)

        self.diffusion_dialog.set_target_size(width, height)

        current_layer = current_document.activeNode()
        pixel_bytes = current_layer.pixelData(x, y, width, height)  # BGRA pixels
        # TODO support other formats than rgba
        image = Image.frombytes('RGBA', (width, height), pixel_bytes, 'raw', 'BGRA')
        self.diffusion_dialog.set_source_image(image)

        self.diffusion_dialog.set_mode(DiffusionMode.IMAGE_TO_IMAGE)
        if not self.diffusion_dialog.exec():
            return

        self.insert_layers_from_diffusion()

    def inpaint(self):
        current_document = Krita.instance().activeDocument()
        if not current_document:
            return

        x, y, width, height = self._get_document_selection(current_document)

        self.diffusion_dialog.set_target_size(width, height)

        current_layer = current_document.activeNode()
        pixel_bytes = current_layer.pixelData(x, y, width, height)  # BGRA pixels
        # TODO support other formats than rgba
        image = Image.frombytes('RGBA', (width, height), pixel_bytes, 'raw', 'BGRA')
        self.diffusion_dialog.set_source_image(image)
        for layer in current_layer.childNodes():
            if layer.type() == 'transparencymask':
                mask = layer
                break
        else:
            return

        mask_pixel_bytes = mask.pixelData(x, y, width, height)  # BGRA pixels
        mask_image = Image.frombytes('L', (width, height), mask_pixel_bytes, 'raw')
        self.diffusion_dialog.set_mask(ImageOps.invert(mask_image))

        self.diffusion_dialog.set_mode(DiffusionMode.INPAINT)
        if not self.diffusion_dialog.exec():
            return

        self.insert_layers_from_diffusion(below=True)

    def upscale(self):
        current_document = Krita.instance().activeDocument()
        if not current_document:
            return

        if not self.diffusion_dialog.exec():
            return

        print('upscale')

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
