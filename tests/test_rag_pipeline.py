import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath("."))

from src.core.document_parser import ParserRegistry
from src.core.chunker import TextChunker
from src.agents.rag_pipeline import RAGPipeline
from src.core.fts_searcher import FTSSearcher
from src.core.vector_store import VectorStore
from src.core.embedder import LocalEmbedder
from src.core.llm_client import LLMClient

def test_full_rag_pipeline():
    # 1. 准备假数据：写入一个 Markdown
    test_space = "test-space-rag-001"
    doc_id = "doc-rag-001"
    
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding='utf-8') as f:
        md_content = """# 苹果公司简介
苹果公司（Apple Inc.）是美国的一家跨国科技公司，总部位于加利福尼亚州的库比蒂诺。它是全球收入最大的信息技术公司。
# 产品线
苹果的主要产品包括iPhone智能手机、iPad平板电脑、Mac个人电脑、iPod便携式媒体播放器、Apple Watch智能手表和Apple TV数字媒体播放器。
        """
        f.write(md_content)
        temp_path = f.name

    try:
        # 2. 解析和分块
        print("Parsing document...")
        doc = ParserRegistry.parse(temp_path)
        chunker = TextChunker()
        refined_chunks = chunker.chunk(doc.chunks)
        assert len(refined_chunks) > 0
        
        # 3. 初始化所有组件
        fts = FTSSearcher()
        vs = VectorStore()
        embedder = LocalEmbedder()
        
        # 注意 LLM 的假密钥处理已经在客户端内进行
        llm = LLMClient()
        
        # 4. 写入检索引擎 
        # FTS5
        print("Adding to FTS5...")
        # 为了兼容之前的测试，我们重新调整入库参数
        for rc in refined_chunks:
            fts.add_chunk(doc_id, test_space, rc.chunk_index, rc.content)
            
        # Vector Store
        print("Generating embeddings and adding to VectorStore...")
        contents = [rc.content for rc in refined_chunks]
        indices = [rc.chunk_index for rc in refined_chunks]
        embeddings = embedder.embed_documents(contents)
        vs.add_chunks(test_space, doc_id, embeddings, contents, indices)
        
        # 5. 测试 RAG Pipeline 融合检索
        pipeline = RAGPipeline(vs, fts, embedder, llm)
        
        print("Testing retrieval fusion...")
        query = "苹果公司主要生产哪些设备？"
        results = pipeline.retrieve(query, test_space)
        assert len(results) > 0
        print(f"RRF Fusion top result: {results[0]['content']}")

        # 6. 测试上下文构建
        context = pipeline.build_prompt_context(results)
        assert "iPhone" in context 
        
        print("Context Built successfully.")
        
        # 7. 清理测试数据
        vs.delete_collection(test_space)
        fts.delete_document(doc_id)
        
    finally:
        os.remove(temp_path)

if __name__ == "__main__":
    test_full_rag_pipeline()
    print("Full RAG Pipeline test passed!")
