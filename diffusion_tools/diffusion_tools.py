import io

from PIL import Image
from PyQt5 import uic
from PyQt5.QtWidgets import QMessageBox

from krita import Extension, DockWidget, Krita
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

    def insert_layers_from_diffusion(self):
        current_document = Krita.instance().activeDocument()
        # TODO selection if any
        width = current_document.width()
        height = current_document.height()
        current_node = current_document.activeNode()
        parent = current_node.parentNode()
        for i, image in enumerate(self.diffusion_dialog.result_images):
            new_node = current_document.createNode(f'diffusion {i}', 'paintLayer')
            pixel_bytes = image.convert('RGBA').resize((width, height)).tobytes('raw', 'BGRA')
            new_node.setPixelData(pixel_bytes, 0, 0, width, height)
            parent.addChildNode(new_node, current_node)

        current_document.refreshProjection()

    def text_to_image(self):
        current_document = Krita.instance().activeDocument()
        if not current_document:
            return

        width = current_document.width()
        height = current_document.height()
        self.diffusion_dialog.set_target_size(width, height)

        self.diffusion_dialog.set_mode(DiffusionMode.TEXT_TO_IMAGE)
        if not self.diffusion_dialog.exec():
            return

        self.insert_layers_from_diffusion()

    def image_to_image(self):
        current_document = Krita.instance().activeDocument()
        if not current_document:
            return

        width = current_document.width()
        height = current_document.height()
        self.diffusion_dialog.set_target_size(width, height)

        current_layer = current_document.activeNode()
        # TODO get selection if any
        pixel_bytes = current_layer.pixelData(0, 0, width, height)  # BGRA pixels
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

        self.diffusion_dialog.set_mode(DiffusionMode.INPAINT)
        if self.diffusion_dialog.exec():
            return

        self.insert_layers_from_diffusion()

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
