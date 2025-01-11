import sys
from typing import Mapping

import numpy as np
import pyaudio
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Voice Training Overlay')
        button = QPushButton('Press me!')

        self.setFixedSize(QSize(400, 300))
        self.setCentralWidget(button)

        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            print(i, p.get_device_info_by_index(i))
        default_input_index = p.get_default_input_device_info()['index']
        print(f'Default device at index {default_input_index}')

        self.stream = p.open(
            rate=48000,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=default_input_index,
            stream_callback=self._on_pyaudio_received
        )
        self.stream.start_stream()

    def _on_pyaudio_received(self, in_data: bytes | None, frame_count: int, time_info: Mapping[str, float], status: int):
        num_bytes = len(in_data)
        bytes_per_sample = 2
        bytes_per_frame = 2
        num_samples = num_bytes // bytes_per_sample

        data: np.ndarray = np.frombuffer(in_data, np.int16)
        #data = data - half_size
        new_data = data / float(np.iinfo(np.int16).max)
        print(f'{new_data.min()=}, {new_data.max()=}')

        #print(f'{type(in_data)=}, {type(frame_count)=}, {type(time_info)=}, {type(status)=}')
        return None, pyaudio.paContinue


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == '__main__':
    main()
