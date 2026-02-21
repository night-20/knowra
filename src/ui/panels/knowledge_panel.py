from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QLabel, QFrame, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.ui.widgets.dropzone import DropZoneWidget
from src.ui.widgets.toast import ToastNotification
from src.core.document_parser import ParserRegistry
from src.core.vector_store import VectorStore
from src.core.fts_searcher import FTSSearcher
from src.core.embedder import LocalEmbedder
from src.core.chunker import TextChunker
from src.models import KnowledgeSpace, Document
from loguru import logger
import uuid
import os

class DocumentImportWorker(QThread):
    """文档导入、解析和写入向量与 FTS5 的后台线程"""
    
    # 进度：(百分比: int, 提示消息: str)
    progress_updated = pyqtSignal(int, str)
    # 完成：(成功列表, 失败字典)
    finished_import = pyqtSignal(list, dict)
    
    def __init__(self, file_paths: list, space_id: str):
        super().__init__()
        self.file_paths = file_paths
        self.space_id = space_id
        self._cancelled = False
        
        # 为了不互相干扰并在子线程中独立运行，线程应持有或即时创建自己的实例
        self.fts = FTSSearcher()
        self.vs = VectorStore()
        self.embedder = LocalEmbedder()
        self.chunker = TextChunker()

    def run(self):
        success = []
        failed = {}
        total = len(self.file_paths)
        
        for idx, path in enumerate(self.file_paths):
            if self._cancelled:
                break
                
            filename = os.path.basename(path)
            self.progress_updated.emit(int((idx / total) * 100), f"正在抽取解析: {filename}")
            
            try:
                # 1. 解析原始文档
                parsed_doc = ParserRegistry.parse(path)
                
                # 2. 从句段整理为 Token Size 合规的小块
                self.progress_updated.emit(int(((idx + 0.3) / total) * 100), f"正在计算分块: {filename}")
                chunks = self.chunker.chunk(parsed_doc.chunks)
                
                # 3. 保存逻辑元数据到 SQLite
                # 这应该根据实际业务需求做去重或检查，简单起见我们每次直接生成新ID
                doc_record = Document.create(
                    space_id=self.space_id,
                    filename=filename,
                    file_type=parsed_doc.file_type,
                    file_path=path,
                    file_hash="mock_hash", # 简化，如果需要可以对文件算 md5
                    word_count=sum([len(c.content) for c in chunks]),
                    is_indexed=False
                )
                doc_id = doc_record.id
                
                # 4. 嵌入生成与向量化存入
                self.progress_updated.emit(int(((idx + 0.5) / total) * 100), f"正在建立 AI 向量: {filename}")
                contents = [c.content for c in chunks]
                indices = [c.chunk_index for c in chunks]
                
                embeddings = self.embedder.embed_documents(contents)
                self.vs.add_chunks(self.space_id, doc_id, embeddings, contents, indices)
                
                # 5. 全文搜索分词存入
                self.progress_updated.emit(int(((idx + 0.8) / total) * 100), f"正在建立全文索引: {filename}")
                for rc_idx, rc in enumerate(chunks):
                    # FTS 中的 index 与源保持一致，这里偷懒用顺序 rc_idx 保证不出错
                    self.fts.add_chunk(doc_id, self.space_id, rc_idx, rc.content)
                    
                doc_record.is_indexed = True
                doc_record.save()
                
                success.append(filename)
                
            except Exception as e:
                logger.error(f"Import failed for {path}: {e}", exc_info=True)
                failed[filename] = str(e)
                
        # 100%
        self.progress_updated.emit(100, f"处理完毕。成功 {len(success)} 个，失败 {len(failed)} 个。")
        self.finished_import.emit(success, failed)


class KnowledgePanelWidget(QWidget):
    """中间的知识库空间与文档管理 (Panel 3)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        # 默认空间由 Main Window 选择设定
        self.current_space = None

    def switch_space(self, space_id: str):
        space = KnowledgeSpace.get_or_none(KnowledgeSpace.id == space_id)
        if space:
            self.current_space = space
            self.space_lbl.setText(f"属于分类: {space.name}")
            self.drop_zone.setEnabled(True)
            self._load_docs()
        else:
            self.current_space = None
            self.space_lbl.setText("请在左侧选择分类知识库")
            self.doc_list.clear()
            self.drop_zone.setEnabled(False)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header
        header_lbl = QLabel("📖 文档与细节")
        header_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #2b2b2b;")
        layout.addWidget(header_lbl)
        
        self.space_lbl = QLabel("请选择知识库")
        self.space_lbl.setStyleSheet("color: #888888;")
        layout.addWidget(self.space_lbl)
        
        # 拖拽上传区
        self.drop_zone = DropZoneWidget()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        self.drop_zone.setFixedHeight(120)
        layout.addWidget(self.drop_zone)
        
        # 导入进度展现区 (正常隐藏)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.hide()
        
        self.progress_lbl = QLabel("准备中...")
        self.progress_lbl.setStyleSheet("color: #f9e2af; font-size: 11px;")
        self.progress_lbl.hide()
        
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_lbl)
        
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #313244;")
        layout.addWidget(line)
        
        # 列表区
        list_lbl = QLabel("当前分类包含的文档: ")
        list_lbl.setStyleSheet("font-weight: bold;")
        layout.addWidget(list_lbl)
        
        self.doc_list = QListWidget()
        layout.addWidget(self.doc_list, 1) # stretch=1
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.setProperty("class", "secondary")
        self.refresh_btn.clicked.connect(self._load_docs)
        layout.addWidget(self.refresh_btn)

    def _load_docs(self):
        if not self.current_space:
            return
        self.doc_list.clear()
        docs = Document.select().where(Document.space_id == self.current_space.id)
        for d in docs:
            status = "已索引" if d.is_indexed else "未索引"
            self.doc_list.addItem(f"[{status}] {d.filename}")

    def _on_files_dropped(self, file_paths: list):
        if hasattr(self, 'worker') and self.worker.isRunning():
            ToastNotification.show_toast("当前已有导入任务在进行中，请稍候...", "warning")
            return
            
        ToastNotification.show_toast(f"准备开始导入 {len(file_paths)} 个文件", "info")
        
        self.progress_bar.show()
        self.progress_lbl.show()
        self.progress_bar.setValue(0)
        self.progress_lbl.setText("初始化引擎并连接数据库...")
        self.drop_zone.setText("⏳ 解析引擎独占中，切勿反复拖拽")
        self.drop_zone.setEnabled(False)
        
        # 开启工作线程
        self.worker = DocumentImportWorker(file_paths, self.current_space.id)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.finished_import.connect(self._on_import_finished)
        self.worker.start()
        
    def _on_progress(self, pct: int, text: str):
        self.progress_bar.setValue(pct)
        self.progress_lbl.setText(text)
        
    def _on_import_finished(self, success: list, failed: dict):
        self.progress_bar.hide()
        self.progress_lbl.hide()
        self.drop_zone.setText("📂 拖拽文件或文件夹到此处\n支持 PDF、MD、TXT 等格式")
        self.drop_zone.setEnabled(True)
        
        msg = f"导入结束。成功: {len(success)} 失败: {len(failed)}"
        if failed:
             ToastNotification.show_toast(f"{msg}\n请查看后台日志追踪错误原因", "error")
        else:
             ToastNotification.show_toast(msg, "success")
             
        self._load_docs()
