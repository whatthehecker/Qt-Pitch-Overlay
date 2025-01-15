import sys
from typing import Mapping, Any, Optional

import pyaudio
from PySide6.QtWidgets import QApplication, QMainWindow, QComboBox, QVBoxLayout, QLabel, QWidget

from audio_graph_widget import AudioGraphWidget
from audio_worker import PyAudioWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pyaudio = pyaudio.PyAudio()

        self.setWindowTitle('Voice Training Overlay')

        self.audio_box = QComboBox()
        for device_info in self._get_valid_input_devices():
            self.audio_box.addItem(device_info['name'], userData=device_info['index'])
        default_device = self.pyaudio.get_default_input_device_info()
        print(default_device)
        self.audio_box.setCurrentText(default_device['name'])
        self.audio_box.currentIndexChanged.connect(self._on_device_changed)

        self.volume_label = QLabel('<volume here>')

        layout = QVBoxLayout()
        layout.addWidget(self.audio_box)
        layout.addWidget(self.volume_label)
        self._audio_graph = AudioGraphWidget()
        layout.addWidget(self._audio_graph)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.worker: Optional[PyAudioWorker] = self._create_and_start_worker(self.pyaudio, default_device)

    def _create_and_start_worker(self, audio: pyaudio.PyAudio, device: Mapping[str, Any]):
        worker = PyAudioWorker(audio, device, parent=self)
        worker.audio_chunk_received.connect(self._update_volume_label)
        worker.start()

        return worker

    def _update_volume_label(self, max_value: float):
        self.volume_label.setText(str(max_value))

        self._audio_graph.add_value(max_value)

    def _on_device_changed(self, index: int):
        device_name = self.audio_box.itemText(index)
        device_index = self.audio_box.itemData(index)
        device = self.pyaudio.get_device_info_by_index(device_index)
        print(device_name, device_index, device['maxInputChannels'])

        if self.worker is not None:
            self.worker.stop()

        self.worker = self._create_and_start_worker(self.pyaudio, device)

    def _get_valid_input_devices(self):
        valid_input_devices = []
        for i in range(self.pyaudio.get_device_count()):
            device_info = self.pyaudio.get_device_info_by_index(i)
            # Filter out non-input devices and virtual devices which have copious amounts of channels.
            if 0 < device_info['maxInputChannels'] < 3:
                valid_input_devices.append(device_info)
        return valid_input_devices


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == '__main__':
    main()
