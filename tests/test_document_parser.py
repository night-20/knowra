import os
import sys

sys.path.insert(0, os.path.abspath("."))

from src.core.document_parser import ParserRegistry
from src.core.chunker import TextChunker
import pytest
import tempfile

def test_markdown_parser_and_chunker():
    # 创建一个测试 md 文件
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding='utf-8') as f:
        md_content = """# Title 1
This is a small paragraph under title 1.
# Title 2
"""
        # 生成一段比较长的文本，超过 512 token 以验证分割
        long_text = "中国" * 800
        md_content += long_text
        
        f.write(md_content)
        temp_path = f.name

    try:
        # 测试解析
        print(f"Testing markdown parsing on {temp_path}")
        parsed_doc = ParserRegistry.parse(temp_path)
        
        assert parsed_doc.file_type == "markdown"
        assert len(parsed_doc.chunks) == 2
        assert parsed_doc.chunks[0].section == "Title 1"
        assert parsed_doc.chunks[1].section == "Title 2"

        # 测试分块
        print("Testing text chunking...")
        chunker = TextChunker()
        refined_chunks = chunker.chunk(parsed_doc.chunks)
        
        # 由于原本只有两个chunk，但是第二个包含 800 个字，超过了 512 的大小，会被强制拆分
        assert len(refined_chunks) > 2
        
        # 验证每个块不要超过 chunk_size 太多
        for rc in refined_chunks:
            tokens = chunker._estimate_tokens(rc.content)
            print(f"Refined chunk token estimated: {tokens}")
            assert tokens <= TextChunker.CHUNK_SIZE * 1.5

        print("Markdown parse and chunk test passed!")
    finally:
        os.remove(temp_path)

if __name__ == "__main__":
    test_markdown_parser_and_chunker()
