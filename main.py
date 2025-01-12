import sys
from typing import Mapping, Any, Optional

import numpy as np
import pyaudio
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QComboBox, QVBoxLayout, QLabel, QWidget


class PyAudioWorker(QThread):
    audio_chunk_received = Signal(float)

    def __init__(self, audio: pyaudio.PyAudio, device: Mapping[str, Any], /, parent=None):
        super().__init__(parent=parent)
        self.pyaudio = audio
        self.device = device

        self.running = False
        self.stream: Optional[pyaudio.Stream] = None

    def _on_audio_received(self, in_data: bytes | None, frame_count: int, time_info: Mapping[str, float], status: int):
        num_bytes = len(in_data)
        if num_bytes <= 0:
            return

        data: np.ndarray = np.frombuffer(in_data, np.int16)
        new_data = (data / float(np.iinfo(np.int16).max)).clip(min=-1.0, max=1.0)
        # print(f'{new_data.min()=}, {new_data.max()=}')
        max_value = new_data.max()
        print(max_value)

        self.audio_chunk_received.emit(max_value)

        return None, (pyaudio.paContinue if self.running else pyaudio.paComplete)

    def stop(self):
        if self.stream is not None:
            self.stream.stop_stream()
        self.running = False

    def run(self):
        self.running = True

        index = self.device['index']
        sample_rate = int(self.device['defaultSampleRate'])

        self.stream = self.pyaudio.open(
            rate=sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=index,
            stream_callback=self._on_audio_received
        )


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

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.worker: Optional[PyAudioWorker] = self._create_and_start_worker(self.pyaudio, default_device)

    def _create_and_start_worker(self, audio: pyaudio.PyAudio, device: Mapping[str, Any]):
        worker = PyAudioWorker(audio, device, parent=self)
        worker.audio_chunk_received.connect(self._update_volume_label)
        # TODO: handle exceptions when this fails, e. g. when device is not available or similar and change back to previous or any other device in UI!
        worker.start()

        return worker

    def _update_volume_label(self, max_value: float):
        self.volume_label.setText(str(max_value))

    def _on_device_changed(self, index: int):
        device_name = self.audio_box.itemText(index)
        device_index = self.audio_box.itemData(index)
        device = self.pyaudio.get_device_info_by_index(index)
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
