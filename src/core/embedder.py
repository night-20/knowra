import os
from typing import List
from src.config.constants import MODELS_DIR, DEFAULT_SETTINGS
from src.config.settings import settings
from loguru import logger

# Delay loading heavy models until actual use, or in a background thread
class LocalEmbedder:
    def __init__(self, model_name: str = None):
        if model_name is None:
            model_name = settings.get("embedding", "model", DEFAULT_SETTINGS["embedding"]["model"])
        
        self.model_name = model_name
        self.model = None

    def _load_model(self):
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}...")
            MODELS_DIR.mkdir(parents=True, exist_ok=True)
            # Set cache folder for huggingface/sentence-transformers
            os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(MODELS_DIR)
            
            try:
                from sentence_transformers import SentenceTransformer
                # device: automatically use cuda if available, otherwise cpu
                self.model = SentenceTransformer(self.model_name, cache_folder=str(MODELS_DIR))
                logger.info(f"Embedding model {self.model_name} loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise e

    def embed_query(self, text: str) -> List[float]:
        """为单条查询生成向量，通常以 list 形式返回供 ChromaDB 消费"""
        self._load_model()
        # BGE 模型建议查询语句带上特殊前缀以提升检索效果，虽然此处按规则保留原句
        # 可选前缀: "为这个句子生成表示以用于检索相关文章："
        prefix = "为这个句子生成表示以用于检索相关文章：" if "bge" in self.model_name.lower() else ""
        query_text = f"{prefix}{text.strip()}"
        
        vector = self.model.encode([query_text], normalize_embeddings=True)[0]
        return vector.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """为多篇文档生成向量"""
        self._load_model()
        if not texts:
            return []
        
        # BGE 模型文档切片不需要前缀
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vectors]
