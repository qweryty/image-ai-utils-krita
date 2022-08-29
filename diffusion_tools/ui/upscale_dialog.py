from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

from .utils import get_ui_file_path


class UpscaleDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(get_ui_file_path('upscale_dialog.ui'), self)

    def gobig(self):
        pass

    def upscale(self):
        pass

    def apply(self):
        self.accept()
