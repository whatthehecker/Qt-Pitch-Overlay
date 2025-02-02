import sys
from typing import Mapping, Any, Optional

import pyaudio
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QWidget, QToolButton, QHBoxLayout

from app_settings import AppSettings
from audio_display_widget import AudioDisplayWidget
from audio_worker import PyAudioWorker
from settings_window import SettingsWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pyaudio = pyaudio.PyAudio()

        self.setWindowTitle('Voice Training Overlay')
        self.volume_label = QLabel('<volume here>')

        self.app_settings = AppSettings(self)

        self.settings_window = SettingsWindow(self.app_settings, self.pyaudio, parent=self)
        self.settings_window.hide()

        self.settings_button = QToolButton()
        self.settings_button.setFixedSize(40, 40)
        self.settings_button.setIcon(QIcon('icons/settings.png'))
        self.settings_button.pressed.connect(lambda: self.settings_window.show())
        horizontal_layout = QHBoxLayout()
        horizontal_layout.addStretch()
        horizontal_layout.addWidget(self.settings_button)

        layout = QVBoxLayout()
        layout.addLayout(horizontal_layout)
        layout.addWidget(self.volume_label)
        self._audio_graph = AudioDisplayWidget()
        layout.addWidget(self._audio_graph)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        default_device = self.pyaudio.get_default_input_device_info()
        self.worker: Optional[PyAudioWorker] = self._create_and_start_worker(self.pyaudio, default_device)

    def _create_and_start_worker(self, audio: pyaudio.PyAudio, device: Mapping[str, Any]):
        worker = PyAudioWorker(audio, device, parent=self)
        worker.audio_chunk_received.connect(self._update_volume_label)
        worker.start()

        return worker

    def _update_volume_label(self, max_value: float):
        self.volume_label.setText(str(max_value))

        self._audio_graph.add_value(max_value)

    def _on_device_changed(self, device: Mapping[str, Any]):
        if self.worker is not None:
            self.worker.stop()

        self.worker = self._create_and_start_worker(self.pyaudio, device)


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == '__main__':
    main()
