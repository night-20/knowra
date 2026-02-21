import sqlite3
import jieba
from typing import List, Dict, Any
from src.config.constants import DATA_DIR
from loguru import logger

FTS_DB_PATH = DATA_DIR / "fts.db"

class FTSSearcher:
    def __init__(self, db_path=FTS_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        # 需在对应的线程内创建连接
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """初始化 fts5 虚拟表"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE VIRTUAL TABLE IF NOT EXISTS fts_chunks USING fts5(
                        document_id,
                        space_id,
                        chunk_index UNINDEXED,
                        content,           -- 原始文本
                        tokenized_content  -- 结巴分词后的文本，用于搜索
                    )
                ''')
                conn.commit()
            logger.debug("FTS5 table initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize FTS5 table: {e}")

    def add_chunk(self, document_id: str, space_id: str, chunk_index: int, content: str):
        """添加单个文档块到 FTS 索引中"""
        # 使用 jieba 进行精确分词，并用空格连接
        tokens = " ".join(jieba.cut(content, cut_all=False))
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO fts_chunks (document_id, space_id, chunk_index, content, tokenized_content) VALUES (?, ?, ?, ?, ?)",
                    (document_id, space_id, chunk_index, content, tokens)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error inserting chunk into FTS5: {e}")

    def search(self, query: str, space_id: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """全文搜索"""
        tokens = " ".join(jieba.cut(query, cut_all=False))
        # 转换为 fts5 匹配模式
        match_query = " OR ".join([f'"{token}"' for token in tokens.split() if token.strip()])
        if not match_query:
            return []

        results = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if space_id:
                    # 如果指定了 space_id，用 WHERE 过滤
                    sql = '''
                        SELECT document_id, chunk_index, content, bm25(fts_chunks) AS score 
                        FROM fts_chunks 
                        WHERE fts_chunks MATCH ? AND space_id = ?
                        ORDER BY score ASC 
                        LIMIT ?
                    '''
                    cursor.execute(sql, (match_query, space_id, top_k))
                else:
                    sql = '''
                        SELECT document_id, chunk_index, content, bm25(fts_chunks) AS score 
                        FROM fts_chunks 
                        WHERE fts_chunks MATCH ?
                        ORDER BY score ASC 
                        LIMIT ?
                    '''
                    cursor.execute(sql, (match_query, top_k))
                
                for row in cursor.fetchall():
                    # bm25 返回的 score 是负数，越小越相关
                    results.append({
                        "document_id": row[0],
                        "chunk_index": row[1],
                        "content": row[2],
                        "score": -row[3] # 转换为正数
                    })
            return results
        except Exception as e:
            logger.error(f"FTS5 Search failed: {e}")
            return []

    def delete_document(self, document_id: str):
        """删除某个文档的索引"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM fts_chunks WHERE document_id = ?", (document_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to delete document from FTS5: {e}")
