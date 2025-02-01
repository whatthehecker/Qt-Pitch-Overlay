import pyaudio
from PySide6.QtCore import QSettings, Signal
from PySide6.QtWidgets import QComboBox, QDialog, QVBoxLayout, QCheckBox, QSpinBox, QLabel


class SettingsWindow(QDialog):
    audio_device_changed = Signal(object)

    def __init__(self, settings: QSettings, audio: pyaudio.PyAudio, parent=...):
        super().__init__(parent)
        self.settings = settings
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
        allow_minimize_value = self.settings.value('allowMinimizeToTray', False, bool) \
            if self.settings.contains('allowMinimizeToTray') else False
        self.allow_minimize_checkbox.setDown(allow_minimize_value)

        self.minimum_range_spinner = QSpinBox()
        self.minimum_range_spinner.setValue(50)

        self.maximum_range_spinner = QSpinBox()
        self.maximum_range_spinner.setValue(350)

        self.minimum_target_spinner = QSpinBox()
        self.minimum_target_spinner.setValue(200)

        self.maximum_target_spinner = QSpinBox()
        self.maximum_target_spinner.setValue(250)

        # TODO: connect signals for spinners to functionality
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
        print(value)
        self.settings.setValue('allowMinimizeToTray', value)

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
