from collections import deque

import numpy as np
from PySide6.QtCharts import QChartView, QChart, QLineSeries, QValueAxis
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtWidgets import QWidget, QVBoxLayout, QDial


class AudioGraphWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self._dial = QDial()

        self._chart = QChart()
        self._chart_view = QChartView(self._chart)
        self._chart_view.setMinimumSize(200, 200)
        self._series = QLineSeries()
        self._chart.addSeries(self._series)

        x_axis = QValueAxis()
        x_axis.setLabelFormat('%g')
        x_axis.setRange(0, 100)
        x_axis.setTitleText('Time')

        y_axis = QValueAxis()
        y_axis.setRange(-1, 1)
        y_axis.setTitleText('Audio level')

        self._chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
        self._series.attachAxis(x_axis)

        self._chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)
        self._series.attachAxis(y_axis)

        self._chart.legend().hide()

        self._buffer: deque[float] = deque(maxlen=100)

        layout.addWidget(self._dial)
        layout.addWidget(self._chart_view)

        self.setLayout(layout)

    def add_value(self, value: float):
        self._buffer.append(value)

        self._series.clear()
        for x, y in enumerate(self._buffer):
            self._series.append(QPointF(x, y))
        #x = list(self.buffer)
        #y = [float(x) for x in range(len(self.buffer))]
        #self._series.appendNp(x, y)