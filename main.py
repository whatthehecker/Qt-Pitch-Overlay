import sys
from typing import Optional

import pyaudio
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QToolButton, QHBoxLayout

from app_settings import AppSettings
from audio_display_widget import AudioDisplayWidget
from audio_provider import AudioProvider, AudioDevice
from audio_worker import AudioWorker
from settings_window import SettingsWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._audio_provider = AudioProvider(pyaudio.PyAudio())

        self.setWindowTitle('Voice Training Overlay')

        self.app_settings = AppSettings(self)

        self.settings_window = SettingsWindow(self.app_settings, self._audio_provider, parent=self)
        self.settings_window.frequencies_changed.connect(self._update_audio_widget)
        self.settings_window.hide()

        self.settings_button = QToolButton()
        self.settings_button.setFixedSize(40, 40)
        self.settings_button.setIcon(QIcon('icons/settings.png'))
        self.settings_button.clicked.connect(lambda: self.settings_window.show())

        self.pin_button = QToolButton()
        self.pin_button.setFixedSize(40, 40)
        self.pin_button.setIcon(QIcon('icons/pin.png'))
        self.pin_button.setCheckable(True)
        self.pin_button.clicked.connect(self._on_pin_pressed)

        horizontal_layout = QHBoxLayout()
        horizontal_layout.addWidget(self.pin_button)
        horizontal_layout.addStretch()
        horizontal_layout.addWidget(self.settings_button)

        layout = QVBoxLayout()
        layout.addLayout(horizontal_layout)
        self._audio_display = AudioDisplayWidget(
            range_min=self.app_settings.minimum_display_frequency,
            range_max=self.app_settings.maximum_display_frequency,
            target_min=self.app_settings.minimum_target_frequency,
            target_max=self.app_settings.maximum_target_frequency,
        )
        layout.addWidget(self._audio_display)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.worker: Optional[AudioWorker] = None
        default_device = self._audio_provider.get_default_input_device()
        if default_device is not None:
            self.worker = self._create_and_start_worker(default_device)

    def _on_pin_pressed(self, pressed: bool):
        self.pin_button.setChecked(pressed)
        if pressed:
            new_flags = self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        else:
            new_flags = self.windowFlags() ^ Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(new_flags)
        # Updating flags means recreating the window, which means it needs to be shown again.
        self.show()

    def _update_audio_widget(self):
        self._audio_display.update_y_axis(
            range_min=self.app_settings.minimum_display_frequency,
            range_max=self.app_settings.maximum_display_frequency,
            target_min=self.app_settings.minimum_target_frequency,
            target_max=self.app_settings.maximum_target_frequency,
        )

    def _create_and_start_worker(self, device: AudioDevice):
        worker = AudioWorker(self._audio_provider, device, parent=self)
        worker.audio_chunk_received.connect(self._update_volume_label)
        worker.start()

        return worker

    def _update_volume_label(self, x: float, y: Optional[float]):
        self._audio_display.add_value(x, y if y is not None else 0)

    def _on_device_changed(self, device: AudioDevice):
        if self.worker is not None:
            self.worker.stop()

        self.worker = self._create_and_start_worker(device)


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == '__main__':
    main()
