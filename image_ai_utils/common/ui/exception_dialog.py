from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QPlainTextEdit

from ..utils import get_ui_file_path


class ExceptionDialog(QDialog):
    message_plain_text_edit: QPlainTextEdit

    def __init__(self, message):
        super().__init__()
        uic.loadUi(get_ui_file_path('exception_dialog.ui'), self)
        self.message_plain_text_edit.setPlainText(message)
