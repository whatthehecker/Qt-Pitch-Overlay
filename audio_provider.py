"""
Wrapper around PyAudio functionality to make it more user-friendly.
"""
from dataclasses import dataclass
from typing import Mapping, Any, Callable

import pyaudio


@dataclass
class AudioDevice:
    index: int
    name: str

    @staticmethod
    def from_pyaudio_device(pyaudio_device: Mapping[str, Any]):
        return AudioDevice(
            index=pyaudio_device['index'],
            name=pyaudio_device['name']
        )


AudioReceivedCallback = Callable[[bytes | None, int, Mapping[str, float], int], tuple[bytes | None, int]]


class AudioProvider:
    SAMPLE_RATE = 16_000

    def __init__(self, audio: pyaudio.PyAudio):
        self._pyaudio = audio
        self.current_device: AudioDevice | None = None

        self._stream: pyaudio.Stream | None = None

    def get_default_input_device(self) -> AudioDevice | None:
        try:
            default_pyaudio_device = self._pyaudio.get_default_input_device_info()
            return AudioDevice.from_pyaudio_device(default_pyaudio_device)
        except IOError:
            # TODO: log that there was no device available
            return None

    def get_device_by_index(self, index: int) -> AudioDevice | None:
        return next(
            (device for device in self.get_valid_input_devices() if device.index == index),
            None
        )

    def get_valid_input_devices(self) -> list[AudioDevice]:
        valid_input_devices = []
        for i in range(self._pyaudio.get_device_count()):
            device_info = self._pyaudio.get_device_info_by_index(i)
            # Filter out non-input devices and virtual devices which have copious amounts of channels.
            if 0 < device_info['maxInputChannels'] < 3:
                device = AudioDevice.from_pyaudio_device(device_info)
                valid_input_devices.append(device)
        return valid_input_devices

    def stop_stream(self):
        self.current_device = None
        if self._stream is not None:
            self._stream.stop_stream()

    def start_stream(self, device: AudioDevice, callback: AudioReceivedCallback, buffer_length_millis: int = 128):
        """
        Starts streaming audio from the given device.

        :param device: The device to stream from.
        :param callback: Callback that is called whenever enough samples have been buffered.
        :param buffer_length_millis: Length of the buffer in milliseconds. Optimally should be a multiple of 64 which
            is internally used by CREPE to determine pitch values.
        """
        self.stop_stream()

        self.current_device = device
        # TODO: handle exceptions when this fails, e. g. when device is not available or similar and change back to previous or any other device in UI!
        self._stream = self._pyaudio.open(
            rate=AudioProvider.SAMPLE_RATE,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=device.index,
            stream_callback=callback,
            frames_per_buffer=int(AudioProvider.SAMPLE_RATE * (buffer_length_millis / 1000))
        )
