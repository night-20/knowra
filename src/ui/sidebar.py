from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSpacerItem, QSizePolicy, QLabel
from PyQt6.QtCore import pyqtSignal, Qt

class SidebarWidget(QWidget):
    """左侧第一栏：主导航栏（仅图标，极简）"""
    
    # 0=知识库/笔记，1=全局搜索/发现，2=偏好设置
    nav_clicked = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(64)
        self._buttons = []
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(15)
        
        # 顶部 Logo，暂时用文本首字替代
        logo_lbl = QLabel("K")
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl.setStyleSheet("font-size: 24px; font-weight: 900; color: #cc6655; margin-bottom: 20px;")
        layout.addWidget(logo_lbl)
        
        # 中间导航
        # Ima/Claude 风：用emoji或简字替代SVG图标
        nav_items = [
            ("📚", "知识与发现", 0),
            ("💬", "全局对话", 1),
        ]
        
        for icon_text, _tooltip, idx in nav_items:
            btn = QPushButton(icon_text)
            btn.setToolTip(_tooltip)
            btn.setFixedSize(44, 44)
            btn.setStyleSheet("font-size: 20px;")
            btn.clicked.connect(lambda checked, i=idx: self._on_btn_clicked(i))
            layout.addWidget(btn)
            self._buttons.append(btn)
            
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # 底部设置
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setToolTip("配置与 API Key")
        self.settings_btn.setFixedSize(44, 44)
        self.settings_btn.setStyleSheet("font-size: 20px;")
        self.settings_btn.clicked.connect(lambda: self._on_btn_clicked(2))
        layout.addWidget(self.settings_btn)
        self._buttons.append(self.settings_btn)
        
        self.set_active(0)
        
    def _on_btn_clicked(self, index: int):
        self.set_active(index)
        self.nav_clicked.emit(index)
        
    def set_active(self, index: int):
        # 0 和 1 号按钮切换激活态，2 号不持久高亮
        if index in [0, 1]:
            for i, btn in enumerate(self._buttons):
                if i < 2:
                    btn.setProperty("active", "true" if i == index else "false")
                    btn.style().unpolish(btn)
                    btn.style().polish(btn)
