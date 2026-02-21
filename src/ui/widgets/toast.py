from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout
from PyQt6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, Qt
from PyQt6.QtGui import QColor

class ToastNotification(QWidget):
    """右下角弹出的临时通知"""
    
    TYPES = {
        "success": "#a6e3a1",
        "error": "#f38ba8", 
        "warning": "#f9e2af",
        "info": "#89b4fa",
    }

    def __init__(self, message: str, toast_type: str = "info", parent=None):
        # ToolTip flags allow it to be totally borderless and unmanaged by the parent layout
        super().__init__(parent, Qt.WindowType.ToolTip)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._init_ui(message, toast_type)
        
        # 3秒后自动淡出消失
        QTimer.singleShot(3000, self._fade_out)

    def _init_ui(self, message, toast_type):
        color = self.TYPES.get(toast_type, self.TYPES["info"])
        
        # Container to apply styles and rounded corners
        self.container = QWidget(self)
        self.container.setStyleSheet(f"""
            QWidget {{
                background-color: #313244;
                border: 1px solid #45475a;
                border-left: 4px solid {color};
                border-radius: 8px;
            }}
            QLabel {{
                color: #cdd6f4;
                font-size: 13px;
                border: none;
                background: transparent;
            }}
        """)
        
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(12, 12, 16, 12)
        
        label = QLabel(message)
        label.setWordWrap(True)
        label.setMinimumWidth(200)
        label.setMaximumWidth(350)
        layout.addWidget(label)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)
        
        self.adjustSize()

    def _fade_out(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(500)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim.finished.connect(self.close)
        self.anim.start()

    @staticmethod
    def show_toast(message: str, toast_type: str = "info", parent=None):
        if not parent:
            # 尝试获取当前的 active window
            from PyQt6.QtWidgets import QApplication
            parent = QApplication.activeWindow()

        toast = ToastNotification(message, toast_type, parent)
        toast.setWindowOpacity(0.0)
        if parent:
            rect = parent.geometry()
            x = rect.right() - toast.width() - 20
            y = rect.bottom() - toast.height() - 40
            
            # map to global if parent has a different coordinate space (though geometry() is relative to parent's parent, 
            # for top-level windows, it's global screen coords, which matches ToolTip window type coords)
            toast.move(x, y)
            
        toast.show()
        
        # fade in
        anim = QPropertyAnimation(toast, b"windowOpacity", toast) # parent the animation so it doesn't get GC'd
        anim.setDuration(300)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        anim.start()
        # Keep a reference to prevent garbage collection of animation occasionally
        toast._in_anim = anim
