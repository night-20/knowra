from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QScrollArea, QLabel, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.ui.widgets.streaming_text import StreamingTextEdit
from src.ui.widgets.spinner import LoadingSpinner
from src.ui.widgets.toast import ToastNotification
from src.agents.doc_qa_agent import DocQAAgent
from loguru import logger

class ChatWorker(QThread):
    """后台处理 AI 请求的线程"""
    
    # 定义信号：(内容片段)
    token_received = pyqtSignal(str)
    # 错误信号
    error_occurred = pyqtSignal(str)
    # 结束信号：(完整回答文本, 引用文档元数据数组)
    finished = pyqtSignal(str, list)

    def __init__(self, agent: DocQAAgent, query: str, space_id: str):
        super().__init__()
        self.agent = agent
        self.query = query
        self.space_id = space_id

    def run(self):
        try:
            full_response = ""
            sources = []
            
            # 迭代 stream 流
            for result in self.agent.ask_stream(self.query, self.space_id):
                if result["type"] == "token":
                    token = result["content"]
                    full_response += token
                    self.token_received.emit(token)
                elif result["type"] == "sources":
                    sources = result["data"]
            
            self.finished.emit(full_response, sources)
            
        except Exception as e:
            logger.error(f"ChatWorker Error: {e}", exc_info=True)
            self.error_occurred.emit(str(e))

class ChatMessageWidget(QWidget):
    """表示单条聊天气泡的组件"""
    def __init__(self, role: str, text: str, sources: list = None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 头部 (角色名)
        header = QLabel("用户" if role == "user" else "Knowra 助理")
        header.setStyleSheet("color: #89b4fa; font-weight: bold;" if role == "assistant" else "color: #a6e3a1; font-weight: bold;")
        layout.addWidget(header)
        
        # 内容
        if role == "assistant":
            # 助理的消息默认用支持 Markdown 和流式的框
            self.content_area = StreamingTextEdit()
            self.content_area.set_markdown(text)
            self.content_area.setMinimumHeight(60)
            self.content_area.setStyleSheet("border: none; background: transparent;")
        else:
            self.content_area = QLabel(text)
            self.content_area.setWordWrap(True)
            self.content_area.setStyleSheet("background-color: #313244; padding: 12px; border-radius: 8px;")
        
        layout.addWidget(self.content_area)
        
        # 显示引用来源
        if sources:
            source_text = "来源: " + ", ".join(set([s.get("document_id", "未知") for s in sources]))
            footer = QLabel(source_text)
            footer.setStyleSheet("color: #6c7086; font-size: 11px;")
            layout.addWidget(footer)

class ChatPanelWidget(QWidget):
    """整体的聊天右侧面板"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # 每个知识空间对应的 Agent，避免跨空间串改历史
        # 简单起见，目前单 Agent 演示
        self.agent = DocQAAgent()
        self.current_space_id = "default_space"
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 顶部标题栏
        header_bar = QFrame()
        header_bar.setFixedHeight(50)
        header_bar.setStyleSheet("background-color: #181825; border-bottom: 1px solid #313244;")
        h_layout = QHBoxLayout(header_bar)
        
        title_lbl = QLabel("与知识库对话")
        title_lbl.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.spinner = LoadingSpinner(size=20)
        
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        h_layout.addWidget(self.spinner)
        layout.addWidget(header_bar)
        
        # 中间的滚动对话区
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background-color: #1e1e2e;")
        
        self.history_container = QWidget()
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.history_container)
        
        layout.addWidget(self.scroll_area, 1) # stretch=1
        
        # 底部的输入区
        input_bar = QWidget()
        input_bar.setStyleSheet("background-color: #181825; border-top: 1px solid #313244;")
        i_layout = QHBoxLayout(input_bar)
        i_layout.setContentsMargins(15, 15, 15, 15)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("询问有关当前知识库的内容，按 Enter 发送...")
        self.input_field.setFixedHeight(40)
        self.input_field.returnPressed.connect(self._send_message)
        
        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedHeight(40)
        self.send_btn.setFixedWidth(80)
        self.send_btn.clicked.connect(self._send_message)
        
        i_layout.addWidget(self.input_field)
        i_layout.addWidget(self.send_btn)
        
        layout.addWidget(input_bar)
        
        # 初始化一条欢迎语
        self._add_message("assistant", "您好，我是 Knowra 知识助理。在这个空间导入了文档后，您可以随时向我提问。")

    def _add_message(self, role: str, text: str, sources=None) -> ChatMessageWidget:
        msg = ChatMessageWidget(role, text, sources)
        self.history_layout.addWidget(msg)
        
        # 滚动到底部
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
        return msg

    def _send_message(self):
        query = self.input_field.text().strip()
        if not query:
            return
            
        # 屏蔽输入防止重复并发操作
        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.spinner.start()
        
        # 添加用户消息气泡
        self._add_message("user", query)
        
        # 预留给 AI 回复的流式气泡 (text 置空，通过内部组件的指针进行插入)
        self.curr_ai_msg = self._add_message("assistant", "")
        
        # 启动 QThread
        self.worker = ChatWorker(self.agent, query, self.current_space_id)
        self.worker.token_received.connect(self.curr_ai_msg.content_area.append_token)
        self.worker.error_occurred.connect(self._on_worker_error)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()
        
    def _on_worker_error(self, err_msg: str):
        ToastNotification.show_toast(f"AI 回复出错: {err_msg}", "error")
        self._reset_input_state()
        
    def _on_worker_finished(self, full_text: str, sources: list):
        self.curr_ai_msg.content_area.finish_stream() # 执行美化排版渲染
        
        # 如果携带来源并需要更新 Footer（因为气泡已经在之前生成，这里简单替换文字或在实际业务中动态新增 Footer）
        # 简单起见我们将来源追加到结尾或依赖气泡实现动态来源注入设计。
        if sources:
             source_text = "\n\n*参考资料: " + ", ".join(set([s.get("document_id", "文档") for s in sources])) + "*"
             self.curr_ai_msg.content_area._buffer += source_text
             self.curr_ai_msg.content_area.finish_stream()

        self._reset_input_state()

    def _reset_input_state(self):
        self.spinner.stop()
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()
