from collections import deque

from PySide6.QtCharts import QChartView, QChart, QLineSeries, QValueAxis, QCategoryAxis
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy


class AudioDisplayWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._chart = QChart()
        self._chart_view = QChartView(self._chart)
        self._chart_view.setMinimumSize(200, 200)
        self._series = QLineSeries()
        self._chart.addSeries(self._series)

        x_axis = QValueAxis()
        x_axis.setRange(0, 10)
        x_axis.setGridLineVisible(False)
        x_axis.setLabelsVisible(False)

        self._chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
        self._series.attachAxis(x_axis)

        y_axis = QCategoryAxis()
        y_axis.setLabelsPosition(QCategoryAxis.AxisLabelsPosition.AxisLabelsPositionOnValue)
        y_axis.setRange(50, 350)
        # Mark the pink target region by creating an axis with "checkered" regions and only show three levels,
        # effectively creating only a single region with a pink backdrop.
        y_axis.setShadesBrush((QBrush(QColor(245, 169, 184, 0x55))))
        y_axis.setShadesVisible(True)
        for value in [175, 250, 350]:
            y_axis.append(f'{value} Hz', value)

        self._chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)
        self._series.attachAxis(y_axis)

        self._chart.legend().hide()

        self._buffer: deque[QPointF] = deque(maxlen=100)

        layout = QVBoxLayout()
        layout.addWidget(self._chart_view)
        self.setLayout(layout)

        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.volume_label = QLabel('<volume here>', self)
        self.volume_label.setStyleSheet('QLabel { background-color : red; color : blue; }')
        #self.volume_label.setFixedSize(100, 20)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Move frequency label on top of chart:
        self.volume_label.move(self._chart_view.geometry().center())

    def add_value(self, x: float, y: float):
        self._buffer.append(QPointF(x, y))

        self._series.clear()
        for point in self._buffer:
            self._series.append(point)
        # Make X-axis always show last 10 seconds and the current value a bit from the right border.
        self._chart.axisX().setRange(x - 10, x + 1)

        if y > 0:
            self.volume_label.setText(f'{y:0.4f}')
        # x = list(self.buffer)
        # y = [float(x) for x in range(len(self.buffer))]
        # self._series.appendNp(x, y)
