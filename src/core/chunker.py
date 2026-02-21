from typing import List
from .document_parser import ParsedChunk

class TextChunker:
    """
    滑动窗口分块器
    策略：优先按段落分割，段落过长时按 token 数强制分割
    """
    
    CHUNK_SIZE = 512      # tokens
    OVERLAP = 50          # tokens  
    MIN_SIZE = 50         # tokens
    
    def chunk(self, chunks: List[ParsedChunk]) -> List[ParsedChunk]:
        """对解析后的 chunks 进行二次精细分块"""
        result = []
        for chunk in chunks:
            sub_chunks = self._split_chunk(chunk)
            result.extend(sub_chunks)
        return result
    
    def _split_chunk(self, chunk: ParsedChunk) -> List[ParsedChunk]:
        """将单个 chunk 按 token 数分割"""
        # 用字符数近似估算 token（中文1字≈1token，英文4字≈1token）
        estimated_tokens = self._estimate_tokens(chunk.content)
        
        if estimated_tokens <= self.CHUNK_SIZE:
            return [chunk] if estimated_tokens >= self.MIN_SIZE else []
        
        # 需要分割
        # 中文通常没有空格，单纯用 split() 会导致长串中文被当成一个 word
        # 稳妥起见，可以使用按字符拆分，或是简单地以预估单字符为基准
        text = chunk.content
        result = []
        start = 0
        sub_index = 0
        
        while start < len(text):
            # 找到适合的终点
            end = start
            current_tokens = 0
            
            # 贪婪扩展直到达到目标大小
            while end < len(text):
                # 每步增加一段，比如每次加10个字符，减少循环次数
                step = 10
                next_end = min(end + step, len(text))
                current_tokens = self._estimate_tokens(text[start:next_end])
                if current_tokens > self.CHUNK_SIZE:
                    # 如果超出，按单个字符微调找准边界
                    while end < len(text) and self._estimate_tokens(text[start:end+1]) <= self.CHUNK_SIZE:
                        end += 1
                    break
                else:
                    end = next_end
            
            chunk_text = text[start:end].strip()
            
            if self._estimate_tokens(chunk_text) >= self.MIN_SIZE or end == len(text):
                # 即使末尾不到 min size，但也只能单独成块了，或者合并到前一个（这里简单作为新块）
                if chunk_text:
                    new_chunk = ParsedChunk(
                        content=chunk_text,
                        source_file=chunk.source_file,
                        page_num=chunk.page_num,
                        section=chunk.section,
                        chunk_index=chunk.chunk_index * 100 + sub_index,
                        char_count=len(chunk_text)
                    )
                    result.append(new_chunk)
                    sub_index += 1
            
            if end >= len(text):
                break
                
            # Overlap 退回机制
            # 估算 overlap 的字符数长度
            # 因为 _estimate_tokens 是线性关系，可用比例倒推
            chunk_char_len = end - start
            overlap_char_len = max(1, int(chunk_char_len * (self.OVERLAP / max(1, self._estimate_tokens(chunk_text)))))
            
            start = end - overlap_char_len
            
            # 强制前进防止死循环
            if start <= result[-1].char_count - chunk_char_len + sum(len(c.content) for c in result[:-1]): # roughly
                 pass # better reliable force forward
            if start <= (end - chunk_char_len):  # basically start shouldn't go back further than original start
                start = end - overlap_char_len
            
            # just a safe guard
            if end - start <= 0:
                start = end
        
        return result
    
    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """估算文本 token 数（粗略）"""
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return chinese_chars + other_chars // 4
