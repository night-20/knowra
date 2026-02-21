from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path

class DropZoneWidget(QLabel):
    """文件拖拽导入区域"""
    
    files_dropped = pyqtSignal(list)  # 发送文件路径列表

    SUPPORTED = {'.pdf', '.md', '.txt'}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("📂 拖拽文件或文件夹到此处\n支持 PDF、MD、TXT 等格式")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #45475a;
                border-radius: 12px;
                color: #6c7086;
                font-size: 14px;
                padding: 40px;
                background-color: transparent;
            }
            QLabel:hover { border-color: #89b4fa; color: #89b4fa; background-color: rgba(137, 180, 250, 0.05); }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(self.styleSheet().replace("#45475a", "#89b4fa"))

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace("#89b4fa", "#45475a"))

    def dropEvent(self, event):
        paths = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            p = Path(path)
            if p.is_dir():
                for f in p.rglob("*"):
                    if f.suffix.lower() in self.SUPPORTED:
                        paths.append(str(f))
            elif p.suffix.lower() in self.SUPPORTED:
                paths.append(str(path))
                
        if paths:
            self.files_dropped.emit(paths)
        self.dragLeaveEvent(event)
