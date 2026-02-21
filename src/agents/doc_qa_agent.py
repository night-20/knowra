from typing import List, Dict, Tuple, Iterator
from .rag_pipeline import RAGPipeline
from src.core.vector_store import VectorStore
from src.core.fts_searcher import FTSSearcher
from src.core.embedder import LocalEmbedder
from src.core.llm_client import LLMClient

class DocQAAgent:
    """包装 RAG 流水线的面向 UI 调用交互 Agent"""
    
    def __init__(self, vector_store: VectorStore=None, fts_searcher: FTSSearcher=None, 
                 embedder: LocalEmbedder=None, llm_client: LLMClient=None):
        self.rag = RAGPipeline(
            vector_store or VectorStore(),
            fts_searcher or FTSSearcher(),
            embedder or LocalEmbedder(),
            llm_client or LLMClient()
        )

    def ask(self, query: str, space_id: str, history: List[Dict[str, str]] = None) -> Tuple[List[Dict], Iterator[str]]:
        """
        调用检索和生成。为了保持上下文历史不爆炸，限制 history 轮数。
        返回 (引用的上下文列表, stream 发生器)
        """
        # 裁剪历史记录，只保留最近的5轮（10条）对话
        safe_history = []
        if history:
            safe_history = history[-10:]
            
        retrieved_docs, stream = self.rag.chat_with_rag(query, space_id, safe_history)
        return retrieved_docs, stream
