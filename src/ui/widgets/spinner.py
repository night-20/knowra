from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QColor, QPen
import math

class LoadingSpinner(QWidget):
    """圆形加载动画"""
    
    def __init__(self, parent=None, size=32, color="#89b4fa"):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0
        self._color = QColor(color)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        # 默认不转
        self.hide()

    def _rotate(self):
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self._color, 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Adjusted bounding rect to fit circle properly
        rect = self.rect().adjusted(3, 3, -3, -3)
        
        # Draw arc: angle needs to be in 1/16th of a degree
        painter.drawArc(rect, -self._angle * 16, 270 * 16)

    def start(self):
        self._timer.start(16)  # ~60fps
        self.show()

    def stop(self):
        self._timer.stop()
        self.hide()
