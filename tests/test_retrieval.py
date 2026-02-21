import os
import sys

sys.path.insert(0, os.path.abspath("."))

from src.core.fts_searcher import FTSSearcher
from src.core.vector_store import VectorStore
from src.core.embedder import LocalEmbedder

def test_retrieval_modules():
    print("--- Testing FTS5 Keyword Search ---")
    fts = FTSSearcher()
    
    test_space_id = "test-space-001"
    doc_id = "doc-001"
    
    # 插入一些虚假句子
    fts.add_chunk(doc_id, test_space_id, 0, "Python 是一种广泛使用的高级编程语言，它的设计哲学强调代码的可读性和简洁的语法。")
    fts.add_chunk(doc_id, test_space_id, 1, "Java 也是一种面向对象的编程语言，通常用于企业级应用开发和 Android 开发。")
    fts.add_chunk(doc_id, test_space_id, 2, "在今天的天气非常好，我们去公园散步了。")
    
    # 测试 FTS 搜索
    results = fts.search("编程语言", test_space_id, top_k=5)
    print(f"FTS Search '编程语言' returned {len(results)} results.")
    assert len(results) >= 2
    for res in results:
        print(f" - [Score: {res['score']:.4f}] {res['content']}")

    print("\n--- Testing Vector Storage and Embedding ---")
    embedder = LocalEmbedder()
    vs = VectorStore()
    
    texts = [
        "Python 是一种广泛使用的高级编程语言，它的设计哲学强调代码的可读性和简洁的语法。",
        "Java 也是一种面向对象的编程语言，通常用于企业级应用开发和 Android 开发。",
        "在今天的天气非常好，我们去公园散步了。"
    ]
    
    print("Generating embeddings (this might take a moment based on model caching)...")
    embeddings = embedder.embed_documents(texts)
    
    # Add to Chroma
    vs.add_chunks(test_space_id, doc_id, embeddings, texts, [0, 1, 2])
    
    query = "有一种面向对象的语言经常用来写安卓"
    print(f"Querying vector store with: '{query}'")
    query_emb = embedder.embed_query(query)
    
    v_results = vs.search(test_space_id, query_emb, top_k=2)
    print(f"Vector Search returned {len(v_results)} results.")
    assert len(v_results) > 0
    # 由于查询"安卓"，Java 那句的得分应该最高
    for res in v_results:
        print(f" - [Score: {res['score']:.4f}] {res['content']}")
        
    # Cleanup Vector Store DB collections for test
    vs.delete_collection(test_space_id)
    fts.delete_document(doc_id)
    print("Retrieval Mixed Test Passed.")

if __name__ == "__main__":
    test_retrieval_modules()
