from collections import deque

from PySide6.QtCharts import QChartView, QChart, QLineSeries, QValueAxis, QCategoryAxis
from PySide6.QtCore import Qt, QPointF, QPoint, QRect, QMargins
from PySide6.QtGui import QBrush, QColor, QFontMetrics, QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy


class AudioDisplayWidget(QWidget):
    def __init__(self, range_min: int, range_max: int, target_min: int, target_max: int, parent: QWidget | None = None):
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

        self.y_axis = self._create_y_axis(range_min, range_max, target_min, target_max)
        self._chart.addAxis(self.y_axis, Qt.AlignmentFlag.AlignLeft)
        self._series.attachAxis(self.y_axis)
        self._chart.legend().hide()

        self._buffer: deque[QPointF] = deque(maxlen=100)

        layout = QVBoxLayout()
        layout.addWidget(self._chart_view)
        self.setLayout(layout)

        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.volume_label = QLabel('<volume here>', self)
        #  "border: 1px solid black;" is good for debugging bounds
        self.volume_label.setStyleSheet('QLabel { color: #111; }')
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.volume_label.setContentsMargins(0, 0, 0, 0)
        #self.volume_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.volume_label.setScaledContents(True)
        #self.volume_label.setFixedSize(100, 20)

    def _create_y_axis(self, range_min: int, range_max: int, target_min: int, target_max: int) -> QCategoryAxis:
        y_axis = QCategoryAxis()
        y_axis.setRange(range_min, range_max)
        y_axis.setLabelsPosition(QCategoryAxis.AxisLabelsPosition.AxisLabelsPositionOnValue)
        y_axis.setLabelsVisible(False)
        # Mark the pink target region by creating an axis with "checkered" regions and only show three levels,
        # effectively creating only a single region with a pink backdrop.
        y_axis.setShadesBrush((QBrush(QColor(245, 169, 184, 0x55))))
        y_axis.setShadesVisible(True)
        for value in [target_min, target_max]:
            y_axis.append(f'{value} Hz', value)
        return y_axis

    def update_y_axis(self, range_min: int, range_max: int, target_min: int, target_max: int):
        self._chart.removeAxis(self.y_axis)
        #self._series.detachAxis(self.y_axis)

        self.y_axis = self._create_y_axis(range_min, range_max, target_min, target_max)
        self._chart.addAxis(self.y_axis, Qt.AlignmentFlag.AlignLeft)
        self._series.attachAxis(self.y_axis)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Move frequency label on top of chart:
        MARGIN = 40
        new_geometry = self._chart_view.geometry().marginsRemoved(QMargins(MARGIN, MARGIN, MARGIN, MARGIN))
        self.volume_label.setGeometry(new_geometry)

        # Determine optimal font size by increasing font size until it does not fit the new bounds anymore.
        font = QFont()
        font_size = 1
        while True:
            font.setPixelSize(font_size)
            rect = QFontMetrics(font).boundingRect('999Hz')
            if rect.height() > new_geometry.height() or rect.width() > new_geometry.width():
                break
            font_size += 1
        font.setPixelSize(font_size)
        self.volume_label.setFont(font)

    def add_value(self, x: float, y: float):
        # TODO: if there's a gap (y <= 0) then store the current series and create a new one so that there can be gaps in the display
        self._buffer.append(QPointF(x, y))

        self._series.clear()
        for point in self._buffer:
            self._series.append(point)
        # Make X-axis always show last 10 seconds and the current value a bit from the right border.
        self._chart.axisX().setRange(x - 10, x + 1)

        if y > 0:
            self.volume_label.setText(f'{round(y)}Hz')
        # x = list(self.buffer)
        # y = [float(x) for x in range(len(self.buffer))]
        # self._series.appendNp(x, y)
