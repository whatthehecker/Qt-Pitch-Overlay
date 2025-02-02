from PySide6.QtCore import QSettings, QObject


class Keys:
    ALLOW_MINIMIZE = 'allowMinimizeToTray'
    MINIMUM_DISPLAY_FREQUENCY = 'minimumDisplayFrequency'
    MAXIMUM_DISPLAY_FREQUENCY = 'maximumDisplayFrequency'
    MINIMUM_TARGET_FREQUENCY = 'minimumTargetFrequency'
    MAXIMUM_TARGET_FREQUENCY = 'maximumTargetFrequency'


class AppSettings:
    ORGANIZATION = 'test-organization'
    APPLICATION = 'voice-overlay'

    def __init__(self, parent: QObject | None = None):
        self._settings = QSettings(AppSettings.ORGANIZATION, AppSettings.APPLICATION, parent=parent)

    @property
    def allow_minimize_to_tray(self):
        return self._settings.value(Keys.ALLOW_MINIMIZE, False, bool)

    @allow_minimize_to_tray.setter
    def allow_minimize_to_tray(self, value: bool):
        self._settings.setValue(Keys.ALLOW_MINIMIZE, value)

    @property
    def minimum_display_frequency(self):
        return self._settings.value(Keys.MINIMUM_DISPLAY_FREQUENCY, 50, int)

    @minimum_display_frequency.setter
    def minimum_display_frequency(self, value: int):
        self._settings.setValue(Keys.MINIMUM_DISPLAY_FREQUENCY, value)

    @property
    def maximum_display_frequency(self):
        return self._settings.value(Keys.MAXIMUM_DISPLAY_FREQUENCY, 350, int)

    @maximum_display_frequency.setter
    def maximum_display_frequency(self, value: int):
        self._settings.setValue(Keys.MAXIMUM_DISPLAY_FREQUENCY, value)

    @property
    def minimum_target_frequency(self):
        return self._settings.value(Keys.MINIMUM_TARGET_FREQUENCY, 185, int)

    @minimum_target_frequency.setter
    def minimum_target_frequency(self, value: int):
        self._settings.setValue(Keys.MINIMUM_TARGET_FREQUENCY, value)

    @property
    def maximum_target_frequency(self):
        return self._settings.value(Keys.MAXIMUM_TARGET_FREQUENCY, 320, int)

    @maximum_target_frequency.setter
    def maximum_target_frequency(self, value: int):
        self._settings.setValue(Keys.MAXIMUM_TARGET_FREQUENCY, value)
