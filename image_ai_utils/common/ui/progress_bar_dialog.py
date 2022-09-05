from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QProgressBar

from ..utils import get_ui_file_path


class ProgressBarDialog(QDialog):
    progress_bar: QProgressBar

    def __init__(self):
        super().__init__()
        uic.loadUi(get_ui_file_path('progress_bar_dialog.ui'), self)

    def set_progress(self, progress: float):
        self.progress_bar.setValue(int(progress * 100))
