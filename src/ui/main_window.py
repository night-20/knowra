from PyQt6.QtWidgets import QMainWindow, QSplitter, QWidget, QHBoxLayout, QStackedWidget, QLabel, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QSettings
from .sidebar import SidebarWidget
from .panels.spaces_panel import SpacesPanelWidget
from .panels.knowledge_panel import KnowledgePanelWidget
from .panels.chat_panel import ChatPanelWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Knowra - 知识探索与助理")
        self.setMinimumSize(1200, 700)
        self._restore_geometry()
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. 最窄左侧导航栏
        self.sidebar = SidebarWidget()
        self.sidebar.nav_clicked.connect(self._on_nav_clicked)
        
        # 2. 中右侧主工作区 Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel 2: Spaces 分类面板
        self.spaces_panel = SpacesPanelWidget()
        self.spaces_panel.toggle_requested.connect(self._toggle_spaces_panel)
        # 为不同库的点击传递信号以切换 Panel 3 数据
        self.spaces_panel.space_selected.connect(self._on_space_switched)
        
        # Panel 3: Knowledge 文档列表
        self.knowledge_panel = KnowledgePanelWidget()
        self.knowledge_panel.setMinimumWidth(300)
        
        # Panel 4: Chat 聊天代理
        self.chat_panel = ChatPanelWidget()
        self.chat_panel.setMinimumWidth(350)
        
        self.splitter.addWidget(self.spaces_panel)
        self.splitter.addWidget(self.knowledge_panel)
        self.splitter.addWidget(self.chat_panel)
        
        # 默认空间比例分配 2 : 4 : 4
        self.splitter.setSizes([200, 450, 450])

        main_layout.addWidget(self.sidebar)
        
        # 在 Panel 2 隐藏时显示的展开按钮
        self.expand_btn = QPushButton("▸")
        self.expand_btn.setFixedSize(20, 40)
        self.expand_btn.setToolTip("展开知识库分类")
        self.expand_btn.setStyleSheet("background-color: #f0eee8; color: #888888; border: 1px solid #e5e3dd; border-radius: 4px; border-left: none; border-top-left-radius: 0; border-bottom-left-radius: 0;")
        self.expand_btn.clicked.connect(self._toggle_spaces_panel)
        self.expand_btn.hide()
        
        # 我们用一个横向 layout 包裹 expand_btn 以便挂在 splitter 最左边（这只是一种表现方式，简化处理放在 side bar 和 splitter 之间）
        mid_layout = QVBoxLayout()
        mid_layout.setContentsMargins(0, 10, 0, 0)
        mid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        mid_layout.addWidget(self.expand_btn)
        
        main_layout.addLayout(mid_layout)
        main_layout.addWidget(self.splitter, 1) # stretch 1
        
    def _on_nav_clicked(self, index: int):
        if index == 0:
            # 知识与发现: 确保展开或聚焦中心视图
            pass
        elif index == 1:
            # 全局对话: 类似隐藏左视图
            pass
        elif index == 2:
            # 打开 API Key 填写的模态框
            from .dialogs.settings_dialog import SettingsDialog
            dl = SettingsDialog(self)
            dl.exec()
            
    def _toggle_spaces_panel(self):
        is_visible = self.spaces_panel.isVisible()
        self.spaces_panel.setVisible(not is_visible)
        self.expand_btn.setVisible(is_visible)
        
    def _on_space_switched(self, space_id: str):
        # 让中间面板加载对应 space 的数据
        self.knowledge_panel.switch_space(space_id)
        # 通知右侧聊天面板切换对应的 agent ID
        self.chat_panel.current_space_id = space_id
        
    def _restore_geometry(self):
        settings = QSettings("Knowra", "App")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1300, 800)

    def closeEvent(self, event):
        settings = QSettings("Knowra", "App")
        settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)
