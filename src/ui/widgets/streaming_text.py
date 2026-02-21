from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import pyqtSlot
import markdown

class StreamingTextEdit(QTextEdit):
    """支持流式追加文本并最终渲染 Markdown 的 TextEdit"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self._buffer = ""
        self._is_streaming = False

    def clear_buffer(self):
        """清空内容和缓冲"""
        self._buffer = ""
        self._is_streaming = False
        self.clear()

    @pyqtSlot(str)
    def append_token(self, token: str):
        """接收 AI 流式 token，追加到末尾"""
        if not self._is_streaming:
            self._is_streaming = True
            self.clear() # 开始新流时清空面板
            
        self._buffer += token
        
        # 为了避免重新渲染全部 HTML 带来卡顿，流式时我们只插入纯文本或者做极其简单的增量
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(token)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    @pyqtSlot()
    def finish_stream(self):
        """流结束时，将积累的 buffer 文本利用 python-markdown 进行完整的美化渲染"""
        if not self._buffer:
            return
            
        self._is_streaming = False
        
        # 将 Markdown 转换为 HTML
        # extensions 加入 fenced_code 等支持代码块和高亮
        html_content = markdown.markdown(
            self._buffer,
            extensions=['fenced_code', 'tables', 'nl2br', 'sane_lists']
        )
        
        # 覆写纯文本为渲染后的 HTML
        self.setHtml(f"<div style='font-family: \"Microsoft YaHei UI\", sans-serif; line-height: 1.6;'>{html_content}</div>")
        
        # 保持滚动到底部
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def set_markdown(self, text: str):
        """非流式直接设置渲染文本"""
        self.clear_buffer()
        self._buffer = text
        self.finish_stream()
