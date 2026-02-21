from typing import List, Dict, Any, Iterator
from loguru import logger
from src.core.vector_store import VectorStore
from src.core.fts_searcher import FTSSearcher
from src.core.embedder import LocalEmbedder
from src.core.llm_client import LLMClient

class RAGPipeline:
    """
    混合检索 RAG 流水线
    向量检索 + 关键词检索 → RRF 融合 → Prompt 构建
    """
    
    MAX_CONTEXT_TOKENS = 3000   # 注入 Prompt 的最大上下文 token 数
    TOP_K = 5                   # 每路检索返回数量
    RRF_K = 60                  # RRF 算法参数
    
    def __init__(self, vector_store: VectorStore, fts_searcher: FTSSearcher, embedder: LocalEmbedder, llm_client: LLMClient):
        self.vector_store = vector_store
        self.fts_searcher = fts_searcher
        self.embedder = embedder
        self.llm_client = llm_client
    
    def retrieve(self, query: str, space_id: str) -> List[Dict]:
        """执行混合检索，返回 RRF 融合排序后的结果"""
        
        # 1. 向量检索
        query_embedding = self.embedder.embed_query(query)
        vector_results = self.vector_store.search(space_id, query_embedding, self.TOP_K)
        
        # 2. 关键词检索
        keyword_results = self.fts_searcher.search(query, space_id, self.TOP_K)
        
        # 3. RRF 融合排序
        fused = self._rrf_fusion(vector_results, keyword_results)
        
        # 4. 截断到最大上下文 Token 数
        return self._truncate_by_tokens(fused, self.MAX_CONTEXT_TOKENS)
    
    def _rrf_fusion(self, list1: List[Dict], list2: List[Dict]) -> List[Dict]:
        """
        Reciprocal Rank Fusion
        score = Σ(1 / (k + rank_i))，k=60
        """
        scores: Dict[str, float] = {}
        items: Dict[str, Dict] = {}
        
        for rank, item in enumerate(list1, start=1):
            key = item["content"][:100]  # 用前100字符作为唯一标识
            scores[key] = scores.get(key, 0) + 1 / (self.RRF_K + rank)
            items[key] = item
        
        for rank, item in enumerate(list2, start=1):
            key = item["content"][:100]
            scores[key] = scores.get(key, 0) + 1 / (self.RRF_K + rank)
            items[key] = item
        
        # 按 RRF 分数降序排列
        sorted_keys = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
        return [items[k] for k in sorted_keys]
    
    def _truncate_by_tokens(self, results: List[Dict], max_tokens: int) -> List[Dict]:
        """按 token 预算截断检索结果"""
        selected = []
        total = 0
        for item in results:
            estimated = len(item["content"]) // 3  # 粗略中文估算
            if total + estimated > max_tokens:
                break
            selected.append(item)
            total += estimated
        return selected
    
    def build_prompt_context(self, retrieved: List[Dict]) -> str:
        """将检索结果格式化为 Prompt 上下文"""
        if not retrieved:
            return "（未找到相关文档内容）"
        
        parts = []
        for i, item in enumerate(retrieved, start=1):
            source = "未知来源"
            page = 0
            section = ""
            
            # 由于前面的实现可能返回不同结构的 metadata，在这里先兼容获取一下，
            # 严格按照规范的话 metadata 是有的，如果之前实现没有封装进 metadata 字段，就需要调整。
            # 为了稳妥起见，我们查看之前 fts 和 vector 的返回，它们可能把 document_id 作为 metadata 的一部分。
            doc_id = item.get("document_id", "未知文档ID")
            
            ref = f"[{i}] 来源文档ID：{doc_id}"
            parts.append(f"{ref}\n{item['content']}")
        
        return "\n\n---\n\n".join(parts)
    
    def get_system_prompt(self, custom_prompt: str = "") -> str:
        """获取 DocQA Agent 的 System Prompt"""
        base = """你是一个专业的文档助手。请严格基于以下检索到的文档内容回答用户问题。

规则：
1. 只能基于提供的文档内容作答，不要编造文档中没有的信息
2. 如果文档中没有相关内容，明确回答"文档中未找到相关内容"
3. 回答时在末尾标注信息来源（用[序号]格式）
4. 使用 Markdown 格式让回答更清晰
5. 用中文回答（除非用户用其他语言提问）"""
        
        return custom_prompt or base
    
    def chat_with_rag(self, query: str, space_id: str,
                      history: List[Dict] = None) -> tuple:
        """
        完整 RAG 对话流程
        返回：(retrieved_items, token_stream_generator)
        """
        # 检索
        retrieved = self.retrieve(query, space_id)
        context = self.build_prompt_context(retrieved)
        
        # 构建消息
        system_prompt = self.get_system_prompt()
        full_system = f"{system_prompt}\n\n【检索到的文档内容】\n{context}"
        
        messages = (history or [])[:]
        messages.append({"role": "user", "content": query})
        
        # 流式生成
        stream = self.llm_client.chat_stream(messages, full_system)
        
        return retrieved, stream
