from typing import Optional

from PySide6.QtCore import QSize, QIODevice, QByteArray
from PySide6.QtMultimedia import QAudioFormat, QAudioInput, QMediaDevices, QAudioSource
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Voice Training Overlay')
        button = QPushButton('Press me!')

        self.setFixedSize(QSize(400, 300))

        self.setCentralWidget(button)

        format = QAudioFormat()
        format.setSampleRate(44100)
        format.setChannelCount(1)
        format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        self.audio_format = format

        default_input_device = QMediaDevices.defaultAudioInput()
        print(f'{default_input_device =}')
        self.audio_input = QAudioInput(default_input_device, self)
        self.audio_source = QAudioSource(default_input_device, format, self)
        self.io_device: Optional[QIODevice] = self.audio_source.start()
        if not self.io_device:
            raise RuntimeError('No IO device received for audio device!')
        self.io_device.readyRead.connect(self.read_audio)

    def read_audio(self):
        data: QByteArray = self.io_device.readAll()

        # Sample = one amplitude, frame = multiple samples, one for each channel
        bytes_per_sample = self.audio_format.bytesPerSample()
        bytes_per_frame = self.audio_format.bytesPerFrame()
        num_frames = data.size() // bytes_per_frame

        duration = self.audio_format.durationForBytes(data.size()) / 1_000
        print(f'{num_frames=}, {duration=}')

        min_val, max_val = 10000, -10000
        for frame in range(num_frames):
            for channel in range(self.audio_format.channelCount()):
                value = self.audio_format.normalizedSampleValue(
                    data[frame * bytes_per_frame + channel * bytes_per_sample])
                min_val = min(min_val, value)
                max_val = max(max_val, value)

        print(f'{min_val=}, {max_val=}')


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == '__main__':
    main()
