import pyaudio
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QDialog, QVBoxLayout, QCheckBox, QSpinBox, QLabel

from app_settings import AppSettings


class SettingsWindow(QDialog):
    audio_device_changed = Signal(object)
    minimum_range_changed = Signal(int)
    maximum_range_changed = Signal(int)
    minimum_target_changed = Signal(int)
    maximum_target_changed = Signal(int)

    def __init__(self, app_settings: AppSettings, audio: pyaudio.PyAudio, parent=...):
        super().__init__(parent)
        self.app_settings = app_settings
        self.pyaudio = audio

        self.setWindowTitle('Settings')

        self.device_selector = QComboBox()
        for device_info in self._get_valid_input_devices():
            self.device_selector.addItem(device_info['name'], userData=device_info['index'])
        default_device = self.pyaudio.get_default_input_device_info()
        print(default_device)
        self.device_selector.setCurrentText(default_device['name'])
        self.device_selector.currentIndexChanged.connect(self._on_device_changed)

        self.allow_minimize_checkbox = QCheckBox('Minimize to tray instead of closing')
        self.allow_minimize_checkbox.toggled.connect(self._on_allow_minimize_toggled)
        self.allow_minimize_checkbox.setChecked(self.app_settings.allow_minimize_to_tray)

        self.minimum_range_spinner = QSpinBox()
        self.minimum_range_spinner.setRange(20, 500)
        self.minimum_range_spinner.setValue(self.app_settings.minimum_display_frequency)
        self.minimum_range_spinner.valueChanged.connect(self._on_minimum_range_changed)

        self.maximum_range_spinner = QSpinBox()
        self.maximum_range_spinner.setRange(20, 500)
        self.maximum_range_spinner.setValue(self.app_settings.maximum_display_frequency)
        self.maximum_range_spinner.valueChanged.connect(self._on_maximum_range_changed)

        self.minimum_target_spinner = QSpinBox()
        self.minimum_target_spinner.setRange(20, 500)
        self.minimum_target_spinner.setValue(self.app_settings.minimum_target_frequency)
        self.minimum_target_spinner.valueChanged.connect(self._on_minimum_target_changed)

        self.maximum_target_spinner = QSpinBox()
        self.maximum_target_spinner.setRange(20, 500)
        self.maximum_target_spinner.setValue(self.app_settings.maximum_target_frequency)
        self.maximum_target_spinner.valueChanged.connect(self._on_maximum_target_changed)
        # TODO: ensure that min <= max whenever any of both is changed

        layout = QVBoxLayout()
        layout.addWidget(self.device_selector)
        layout.addWidget(self.allow_minimize_checkbox)
        layout.addWidget(QLabel('Minimum frequency to display:'))
        layout.addWidget(self.minimum_range_spinner)
        layout.addWidget(QLabel('Maximum frequency to display:'))
        layout.addWidget(self.maximum_range_spinner)
        layout.addWidget(QLabel('Minimum frequency of target:'))
        layout.addWidget(self.minimum_target_spinner)
        layout.addWidget(QLabel('Maximum frequency of target:'))
        layout.addWidget(self.maximum_target_spinner)
        self.setLayout(layout)

    def _on_allow_minimize_toggled(self, value: bool):
        self.app_settings.allow_minimize_to_tray = value

    def _on_minimum_range_changed(self, value: int):
        self.app_settings.minimum_display_frequency = value
        self.minimum_range_changed.emit(value)

    def _on_maximum_range_changed(self, value: int):
        self.app_settings.maximum_display_frequency = value
        self.maximum_range_changed.emit(value)

    def _on_minimum_target_changed(self, value: int):
        self.app_settings.minimum_target_frequency = value
        self.minimum_target_changed.emit(value)

    def _on_maximum_target_changed(self, value: int):
        self.app_settings.maximum_target_frequency = value
        self.maximum_target_changed.emit(value)

    def _on_device_changed(self, index: int):
        device_name = self.device_selector.itemText(index)
        device_index = self.device_selector.itemData(index)
        device = self.pyaudio.get_device_info_by_index(device_index)
        print(device_name, device_index, device['maxInputChannels'])

        self.audio_device_changed.emit(device)

    def _get_valid_input_devices(self):
        valid_input_devices = []
        for i in range(self.pyaudio.get_device_count()):
            device_info = self.pyaudio.get_device_info_by_index(i)
            # Filter out non-input devices and virtual devices which have copious amounts of channels.
            if 0 < device_info['maxInputChannels'] < 3:
                valid_input_devices.append(device_info)
        return valid_input_devices
