import json

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QLineEdit, QMessageBox

from ..client import ImageAIUtilsClient
from ..utils import get_ui_file_path
from ..settings import Settings, SETTINGS_PATH


class SettingsDialog(QDialog):
    url_line_edit: QLineEdit
    username_line_edit: QLineEdit
    password_line_edit: QLineEdit

    def __init__(self):
        super().__init__()
        uic.loadUi(get_ui_file_path('settings_dialog.ui'), self)

    def init_fields(self):
        if Settings.settings() is None:
            return

        self.url_line_edit.setText(Settings.settings().SERVER_URL)
        self.username_line_edit.setText(Settings.settings().USERNAME)
        self.password_line_edit.setText(Settings.settings().PASSWORD)

    def test_connection(self):
        client = ImageAIUtilsClient(
            base_url=self.url_line_edit.text(),
            username=self.username_line_edit.text(),
            password=self.password_line_edit.text()
        )
        success, message = client.test_connection()
        if success:
            message_box = QMessageBox()
            message_box.setIcon(QMessageBox.Information)
            message_box.setWindowTitle('Success')
            message_box.setText('Successfully connected to server')
            message_box.setStandardButtons(QMessageBox.Ok)
            message_box.exec()
        else:
            message_box = QMessageBox()
            message_box.setIcon(QMessageBox.Warning)
            message_box.setWindowTitle('Failed')
            message_box.setText(f'Connection to server failed: {message}')
            message_box.setStandardButtons(QMessageBox.Ok)
            message_box.exec()

    def save(self):
        with open(SETTINGS_PATH, 'w') as f:
            json.dump(
                {
                    'SERVER_URL': self.url_line_edit.text(),
                    'USERNAME': self.username_line_edit.text(),
                    'PASSWORD': self.password_line_edit.text()
                },
                f
            )

    def apply(self):
        self.save()
        Settings.settings()
        self.accept()

