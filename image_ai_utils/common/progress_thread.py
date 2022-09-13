import traceback
from typing import Callable, Dict, Any

from PyQt5.QtCore import QThread, pyqtSignal

from .client import WebSocketException


class ProgressThread(QThread):
    progress_signal = pyqtSignal(float)

    def __init__(self, client_method: Callable, request_data: Dict[str, Any]):
        super().__init__()
        self._request_data = request_data
        self._client_method = client_method
        self.result = None
        self.success = False
        self.error_message = None

    def run(self):
        def progress_callback(progress: float):
            self.progress_signal.emit(progress)

        try:
            self.result = self._client_method(
                progress_callback=progress_callback, **self._request_data
            )
            self.success = True
        except WebSocketException as e:
            self.success = False
            self.error_message = e.message
        except Exception as e:
            self.success = False
            self.error_message = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
