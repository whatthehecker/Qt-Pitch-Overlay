from typing import Mapping, Any

import crepe
import tensorflow as tf
import numpy as np
import pyaudio
from PySide6.QtCore import QThread, Signal

SAMPLE_RATE = 16_000

class PyAudioWorker(QThread):

    audio_chunk_received = Signal(float)

    def __init__(self, audio: pyaudio.PyAudio, device: Mapping[str, Any], /, parent=None):
        super().__init__(parent=parent)
        self.pyaudio = audio
        self.device = device

        self.running = False
        self.stream: pyaudio.Stream | None = None

    def _on_audio_received(self, in_data: bytes | None, frame_count: int, time_info: Mapping[str, float], status: int):
        num_bytes = len(in_data)
        if num_bytes <= 0:
            return

        data: np.ndarray = np.frombuffer(in_data, np.int16)
        new_data = (data / float(np.iinfo(np.int16).max)).clip(min=-1.0, max=1.0)
        # print(f'{new_data.min()=}, {new_data.max()=}')
        max_value = new_data.max()

        time, frequency, confidence, activation = crepe.predict(audio=data, sr=SAMPLE_RATE, verbose=False, step_size=100)
        max_index = np.argmax(confidence)
        max_confidence = confidence[max_index]
        frequency = frequency[max_index]
        print(f'{frequency=} ({max_confidence=})')

        if max_confidence >= 0.5 and 50 < frequency < 350:
            self.audio_chunk_received.emit(frequency)

        return None, (pyaudio.paContinue if self.running else pyaudio.paComplete)

    def stop(self):
        if self.stream is not None:
            self.stream.stop_stream()
        self.running = False

    def run(self):
        self.running = True

        index = self.device['index']
        sample_rate = int(self.device['defaultSampleRate'])

        # TODO: handle exceptions when this fails, e. g. when device is not available or similar and change back to previous or any other device in UI!
        self.stream = self.pyaudio.open(
            rate=SAMPLE_RATE,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=index,
            stream_callback=self._on_audio_received,
            frames_per_buffer=SAMPLE_RATE // 5
        )
