import time
from typing import Mapping, Optional

import crepe
import tensorflow as tf
import numpy as np
import pyaudio
from PySide6.QtCore import QThread, Signal, QObject

from audio_provider import AudioProvider, AudioDevice

SAMPLE_RATE = 16_000


class AudioWorker(QThread):
    audio_chunk_received = Signal(float, float)

    def __init__(self, audio_provider: AudioProvider, device: AudioDevice, parent: QObject | None = None):
        super().__init__(parent=parent)

        self._audio_provider = audio_provider
        self._device = device

        self.running = False
        self._start_time: int | None = None

    def _on_audio_received(self, in_data: bytes | None, frame_count: int, time_info: Mapping[str, float], status: int):
        num_bytes = len(in_data)
        if num_bytes <= 0:
            return

        data: np.ndarray = np.frombuffer(in_data, np.int16)
        _, frequency, confidence, _ = crepe.predict(audio=data, sr=SAMPLE_RATE, verbose=False, step_size=100)
        max_index = np.argmax(confidence)
        max_confidence = confidence[max_index]
        frequency = frequency[max_index]
        # print(f'{frequency=} ({max_confidence=})')

        current_time = time.time() - self._start_time
        # TODO: use frequency bounds as set in settings instead of hardcoded ones
        if max_confidence >= 0.5 and 50 < frequency < 350:
            self.audio_chunk_received.emit(current_time, frequency)
        else:
            self.audio_chunk_received.emit(current_time, None)

        return None, (pyaudio.paContinue if self.running else pyaudio.paComplete)

    def stop(self):
        self.running = False
        self._audio_provider.stop_stream()

    def run(self):
        self.running = True
        self._start_time = time.time()
        self._audio_provider.start_stream(self._device, self._on_audio_received)
