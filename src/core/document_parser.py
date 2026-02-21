from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from loguru import logger
import fitz  # PyMuPDF

@dataclass
class ParsedChunk:
    """解析后的文本块"""
    content: str           # 文本内容
    source_file: str       # 来源文件名
    page_num: int          # 页码（从1开始，无页码则为0）
    section: str           # 章节标题（可为空）
    chunk_index: int       # 在文档中的顺序
    char_count: int        # 字符数

@dataclass  
class ParsedDocument:
    """解析后的完整文档"""
    title: str
    author: str
    file_path: str
    file_type: str
    page_count: int
    chunks: List[ParsedChunk]
    metadata: dict

class BaseParser(ABC):
    """解析器基类"""
    
    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        raise NotImplementedError

class PDFParser(BaseParser):
    
    @property
    def supported_extensions(self):
        return ['.pdf']
    
    def parse(self, file_path: str) -> ParsedDocument:
        doc = fitz.open(file_path)
        chunks = []
        chunk_index = 0
        
        metadata = doc.metadata
        title = metadata.get('title') or Path(file_path).stem
        author = metadata.get('author', '')
        
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if not text.strip():
                continue
            
            # 按段落分割
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            
            for para in paragraphs:
                if len(para) < 20:
                    continue
                chunks.append(ParsedChunk(
                    content=para,
                    source_file=Path(file_path).name,
                    page_num=page_num,
                    section="",
                    chunk_index=chunk_index,
                    char_count=len(para)
                ))
                chunk_index += 1
        
        doc.close()
        return ParsedDocument(
            title=title, author=author, file_path=file_path,
            file_type='pdf', page_count=len(doc),
            chunks=chunks, metadata=metadata
        )

class MarkdownParser(BaseParser):
    
    @property
    def supported_extensions(self):
        return ['.md', '.markdown']
    
    def parse(self, file_path: str) -> ParsedDocument:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        chunks = []
        current_section = ""
        current_content = []
        chunk_index = 0
        
        for line in content.split('\n'):
            if line.startswith('#'):
                if current_content:
                    text = '\n'.join(current_content).strip()
                    if text:
                        chunks.append(ParsedChunk(
                            content=text,
                            source_file=Path(file_path).name,
                            page_num=0,
                            section=current_section,
                            chunk_index=chunk_index,
                            char_count=len(text)
                        ))
                        chunk_index += 1
                current_section = line.lstrip('#').strip()
                current_content = []
            else:
                current_content.append(line)
        
        if current_content:
            text = '\n'.join(current_content).strip()
            if text:
                chunks.append(ParsedChunk(
                    content=text, source_file=Path(file_path).name,
                    page_num=0, section=current_section,
                    chunk_index=chunk_index, char_count=len(text)
                ))
        
        title = Path(file_path).stem
        return ParsedDocument(
            title=title, author='', file_path=file_path,
            file_type='markdown', page_count=0,
            chunks=chunks, metadata={}
        )

class TextParser(BaseParser):
    @property
    def supported_extensions(self):
        return ['.txt']

    def parse(self, file_path: str) -> ParsedDocument:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        chunks = []
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        for i, para in enumerate(paragraphs):
            if len(para) < 20:
                continue
            chunks.append(ParsedChunk(
                content=para,
                source_file=Path(file_path).name,
                page_num=0,
                section="",
                chunk_index=i,
                char_count=len(para)
            ))
            
        title = Path(file_path).stem
        return ParsedDocument(
            title=title, author='', file_path=file_path,
            file_type='text', page_count=0,
            chunks=chunks, metadata={}
        )

class ParserRegistry:
    """解析器注册中心"""
    
    _parsers: dict = {}
    
    @classmethod
    def register(cls, parser: BaseParser):
        for ext in parser.supported_extensions:
            cls._parsers[ext.lower()] = parser
    
    @classmethod
    def get_parser(cls, file_path: str) -> Optional[BaseParser]:
        ext = Path(file_path).suffix.lower()
        return cls._parsers.get(ext)
    
    @classmethod
    def parse(cls, file_path: str) -> ParsedDocument:
        parser = cls.get_parser(file_path)
        if not parser:
            logger.warning(f"Fallback to text parser for file format: {Path(file_path).suffix} at {file_path}")
            parser = TextParser()
        return parser.parse(file_path)

# 自动注册全部支持的内置解析器
ParserRegistry.register(PDFParser())
ParserRegistry.register(MarkdownParser())
ParserRegistry.register(TextParser())
