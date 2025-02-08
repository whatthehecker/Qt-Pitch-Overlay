import os
import time
from typing import Mapping

import crepe
# Needs to be imported here, else crashes due to the TF-invoking code being loaded in another QThread at runtime (?).
import tensorflow as tf
import numpy as np
import pyaudio
from PySide6.QtCore import QThread, Signal, QObject

from tensorflow.keras.layers import Input, Reshape, Conv2D, BatchNormalization
from tensorflow.keras.layers import MaxPool2D, Dropout, Permute, Flatten, Dense
from tensorflow.keras.models import Model

from audio_provider import AudioProvider, AudioDevice

basedir = os.path.dirname(__file__)

SAMPLE_RATE = 16_000


# Copied from crepe/core.py.
def _load_existing_model() -> Model:
    layers = [1, 2, 3, 4, 5, 6]
    filters = [n * 32 for n in [32, 4, 4, 4, 8, 16]]
    widths = [512, 64, 64, 64, 64, 64]
    strides = [(4, 1), (1, 1), (1, 1), (1, 1), (1, 1), (1, 1)]

    x = Input(shape=(1024,), name='input', dtype='float32')
    y = Reshape(target_shape=(1024, 1, 1), name='input-reshape')(x)

    for l, f, w, s in zip(layers, filters, widths, strides):
        y = Conv2D(f, (w, 1), strides=s, padding='same',
                   activation='relu', name="conv%d" % l)(y)
        y = BatchNormalization(name="conv%d-BN" % l)(y)
        y = MaxPool2D(pool_size=(2, 1), strides=None, padding='valid',
                      name="conv%d-maxpool" % l)(y)
        y = Dropout(0.25, name="conv%d-dropout" % l)(y)

    y = Permute((2, 1, 3), name="transpose")(y)
    y = Flatten(name="flatten")(y)
    y = Dense(360, activation='sigmoid', name="classifier")(y)

    model = Model(inputs=x, outputs=y)

    model.load_weights(os.path.join(basedir, 'crepe-models', 'model-full.h5'))
    model.compile('adam', 'binary_crossentropy')

    return model


class AudioWorker(QThread):
    audio_chunk_received = Signal(float, float)

    def __init__(self, audio_provider: AudioProvider, device: AudioDevice, parent: QObject | None = None):
        super().__init__(parent=parent)

        # Work around crepe creating some directories in non-existing paths when run using PyInstaller, simply
        # load the shipped model before any crepe logic could create it using incorrect paths.
        if crepe.core.models['full'] is None:
            crepe.core.models['full'] = _load_existing_model()

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
