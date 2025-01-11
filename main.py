from typing import Optional, Mapping

from PySide6.QtCore import QSize, QIODevice, QByteArray, QMicrophonePermission, Qt
from PySide6.QtMultimedia import QAudioFormat, QMediaDevices, QAudioSource, QAudioInput
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton
import sys
import pyaudio
import numpy as np


class MainWindow(QMainWindow):
    def __init__(self, app: QApplication):
        super().__init__()

        self.app = app

        self._request_permissions()

        self.setWindowTitle('Voice Training Overlay')
        button = QPushButton('Press me!')

        self.setFixedSize(QSize(400, 300))

        self.setCentralWidget(button)

        format = QAudioFormat()
        format.setSampleRate(44100)
        format.setChannelCount(1)
        format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        self.audio_format = format

        print('Available devices:')
        devices = QMediaDevices(self)
        for device in devices.audioInputs():
            print(f'- {device.description()}')

        default_input_device = QMediaDevices.defaultAudioInput()
        print(f'{default_input_device.description()}')

        self.audio_source = QAudioSource(default_input_device, format=default_input_device.preferredFormat(), parent=self)
        self.audio_format = self.audio_source.format()
        print(self.audio_format)
        self.io_device: Optional[QIODevice] = self.audio_source.start()
        if not self.io_device or not self.io_device.isOpen():
            raise RuntimeError('No IO device received for audio device!')
        self.io_device.readyRead.connect(self.read_audio)

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
        #self.stream.start_stream()

    def _request_permissions(self):
        microphone_permission = QMicrophonePermission()
        match self.app.checkPermission(microphone_permission):
            case Qt.PermissionStatus.Undetermined:
                self.app.requestPermission(microphone_permission, self, self._request_permissions)
            case Qt.PermissionStatus.Denied:
                print('Microphone permission was denied!')
                return
            case Qt.PermissionStatus.Granted:
                print('Permission was granted!')

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

    def read_audio(self):
        data: QByteArray = self.io_device.readAll()

        # Sample = one amplitude, frame = multiple samples, one for each channel
        bytes_per_sample = self.audio_format.bytesPerSample()
        bytes_per_frame = self.audio_format.bytesPerFrame()
        num_frames = data.size() // bytes_per_frame

        if num_frames <= 0:
            return

        duration = self.audio_format.durationForBytes(data.size()) / 1_000
        print(f'{num_frames=}, {duration=}')

        min_val, max_val = 10000, -10000
        values = np.frombuffer(data.data(), np.uint16)
        print(f'{len(values)=}')
        print(f'{self.audio_format.channelCount()}')
        for frame in range(num_frames):
            for channel in range(self.audio_format.channelCount()):
                value: int = values[frame * self.audio_format.channelCount() + channel]
                #print(value, type(value))
                normalized = self.audio_format.normalizedSampleValue(bytes(value))
                #print(frame * bytes_per_frame + channel * bytes_per_sample, normalized)
                min_val = min(min_val, normalized)
                max_val = max(max_val, normalized)

        print(f'{min_val=}, {max_val=}')


def main():
    app = QApplication(sys.argv)

    window = MainWindow(app)
    window.show()

    app.exec()


if __name__ == '__main__':
    main()
