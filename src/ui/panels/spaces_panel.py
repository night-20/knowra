from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from src.models import KnowledgeSpace

class SpacesPanelWidget(QWidget):
    """分类导航侧边栏 (Panel 2)"""
    
    space_selected = pyqtSignal(str) # 传递所选 space_id
    toggle_requested = pyqtSignal()  # 请求折叠自己
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("spaces_panel")
        self.setMinimumWidth(180)
        self.setMaximumWidth(300)
        self._buttons = []
        self._init_ui()
        self.load_spaces()
        
    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 20, 15, 20)
        self.layout.setSpacing(10)
        
        # 头部区域：折叠按钮 + 标题
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title_lbl = QLabel("个人知识库")
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #2b2b2b;")
        
        # 侧边栏折叠按钮
        self.toggle_btn = QPushButton("◂")
        self.toggle_btn.setToolTip("折叠面板")
        self.toggle_btn.setFixedSize(28, 28)
        self.toggle_btn.setProperty("class", "icon_button")
        self.toggle_btn.clicked.connect(self.toggle_requested.emit)
        
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.toggle_btn)
        self.layout.addLayout(header_layout)
        
        # 空间列表容器
        self.list_layout = QVBoxLayout()
        self.list_layout.setSpacing(4)
        self.layout.addLayout(self.list_layout)
        
        self.layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # 底部添加空间按钮
        self.add_btn = QPushButton("+ 新建空间")
        self.add_btn.setProperty("class", "secondary")
        self.add_btn.clicked.connect(self._create_new_space)
        self.layout.addWidget(self.add_btn)

    def load_spaces(self):
        # 清空已有
        for btn in self._buttons:
            self.list_layout.removeWidget(btn)
            btn.deleteLater()
        self._buttons.clear()
        
        spaces = KnowledgeSpace.select()
        
        # 如果没有任何空间，创建一个默认的
        if spaces.count() == 0:
            KnowledgeSpace.create(id="default_space", name="我的默认主库")
            spaces = KnowledgeSpace.select()
            
        for space in spaces:
            btn = QPushButton(f"📁 {space.name}")
            btn.clicked.connect(lambda checked, s_id=space.id: self._on_space_clicked(s_id))
            self.list_layout.addWidget(btn)
            self._buttons.append((space.id, btn))
            
        if self._buttons:
            self._on_space_clicked(self._buttons[0][0]) # 默认选中第一个
            
    def _on_space_clicked(self, space_id: str):
        for s_id, btn in self._buttons:
            if s_id == space_id:
                btn.setProperty("active", "true")
            else:
                btn.setProperty("active", "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            
        self.space_selected.emit(space_id)

    def _create_new_space(self):
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "新建知识空间", "空间名称:")
        if ok and text.strip():
            KnowledgeSpace.create(name=text.strip())
            self.load_spaces()
