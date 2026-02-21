import chromadb
from typing import List, Dict, Any, Optional
from src.config.constants import VECTOR_DIR
from loguru import logger

class VectorStore:
    def __init__(self, persist_directory=VECTOR_DIR):
        # 确保目录存在
        persist_directory.mkdir(parents=True, exist_ok=True)
        try:
            self.client = chromadb.PersistentClient(path=str(persist_directory))
            logger.debug(f"ChromaDB PersistentClient initialized at {persist_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB Client: {e}")
            raise e

    def get_or_create_collection(self, space_id: str):
        """按 space_id 隔离每个 Collection"""
        # Collection 名称不能有特殊字符，统一前缀和过滤
        # PRD要求：按 space_id 划分 PersistentClient Collection 相关动作
        collection_name = f"space_{space_id.replace('-', '_')}"
        try:
            # 默认使用 cosine 距离计算相似度
            return self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.error(f"Error getting/creating collection {collection_name}: {e}")
            raise e

    def add_chunks(self, space_id: str, document_id: str, embeddings: List[List[float]], contents: List[str], chunk_indices: List[int]):
        """批量添加文本和向量到 ChromaDB"""
        if not embeddings or not contents:
            return

        collection = self.get_or_create_collection(space_id)
        
        ids = [f"{document_id}_{i}" for i in chunk_indices]
        metadatas = [{"document_id": document_id, "chunk_index": i} for i in chunk_indices]

        try:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas
            )
        except Exception as e:
            logger.error(f"Error adding chunks to ChromaDB collection {space_id}: {e}")
            raise e

    def search(self, space_id: str, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """基于给定的问题嵌入向量，在指定的空间内搜索最相似的段落"""
        collection = self.get_or_create_collection(space_id)
        
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )

            # 组装返回结果结构以匹配需要的情况
            formatted_results = []
            if not results['ids'] or len(results['ids'][0]) == 0:
                return formatted_results

            for idx, doc_id_with_chunk in enumerate(results['ids'][0]):
                formatted_results.append({
                    "document_id": results['metadatas'][0][idx]['document_id'],
                    "chunk_index": results['metadatas'][0][idx]['chunk_index'],
                    "content": results['documents'][0][idx],
                    "score": 1.0 - results['distances'][0][idx] # 假设 cosine，把 distance 转为相似度
                })
                
            return formatted_results
        except Exception as e:
            logger.error(f"ChromaDB Search error: {e}")
            return []

    def delete_document(self, space_id: str, document_id: str):
        """删除特定文档的所有记录"""
        collection = self.get_or_create_collection(space_id)
        try:
            collection.delete(
                where={"document_id": document_id}
            )
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from {space_id}: {e}")

    def delete_collection(self, space_id: str):
        """删除整个知识空间"""
        collection_name = f"space_{space_id.replace('-', '_')}"
        try:
            self.client.delete_collection(name=collection_name)
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {e}")
