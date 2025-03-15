"""
Text chunking functionality.
"""

import re
from typing import List

from documetor.config import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP


class TextChunker:
    """Class to chunk text into smaller pieces"""
    
    def __init__(
        self, 
        chunk_size: int = DEFAULT_CHUNK_SIZE, 
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        strategy: str = "hybrid"
    ):
        """
        Initialize the chunker
        
        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between consecutive chunks
            strategy: Chunking strategy (hybrid, sentence, fixed)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks
        
        Args:
            text: The text to chunk
            
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        if self.strategy == "sentence":
            return self._chunk_by_sentence(text)
        elif self.strategy == "fixed":
            return self._chunk_fixed(text)
        else:  # Default to hybrid approach
            return self._chunk_hybrid(text)
    
    def _chunk_hybrid(self, text: str) -> List[str]:
        """
        Chunk by trying to find natural breaks like newlines or sentences
        
        Args:
            text: Text to chunk
            
        Returns:
            List of chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            # Try to find a good breaking point
            if end < len(text):
                # Look for paragraph break first
                para_break = text.rfind('\n\n', start, end)
                if para_break > start + self.chunk_size // 2:
                    end = para_break + 2
                else:
                    # Look for newline next
                    newline_pos = text.rfind('\n', start, end)
                    if newline_pos > start + self.chunk_size // 2:
                        end = newline_pos + 1
                    else:
                        # Look for sentence end next
                        for sep in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
                            sent_end = text.rfind(sep, start, end)
                            if sent_end > start + self.chunk_size // 2:
                                end = sent_end + len(sep)
                                break
                        else:
                            # Fall back to space
                            space_pos = text.rfind(' ', start, end)
                            if space_pos > start + self.chunk_size // 2:
                                end = space_pos + 1
            
            # Add the chunk
            chunks.append(text[start:end])
            
            # Move start position for next chunk, considering overlap
            start = end - self.chunk_overlap
            
            # Avoid getting stuck in an infinite loop
            if start >= end or end == len(text):
                if end < len(text):
                    start = end  # Skip ahead to avoid being stuck
                else:
                    break
        
        return chunks
    
    def _chunk_by_sentence(self, text: str) -> List[str]:
        """
        Chunk by grouping sentences together
        
        Args:
            text: Text to chunk
            
        Returns:
            List of chunks
        """
        # Split text into sentences
        sentence_endings = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_endings, text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_len = len(sentence)
            
            # Handle very long sentences
            if sentence_len > self.chunk_size:
                # If we have content in the current chunk, add it first
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # Split the long sentence into fixed chunks
                sent_chunks = self._chunk_fixed(sentence)
                chunks.extend(sent_chunks)
                continue
            
            # If adding this sentence would exceed the chunk size, start a new chunk
            if current_length + sentence_len > self.chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                
                # Check if we need overlap
                if self.chunk_overlap > 0:
                    # Determine how many sentences to keep for overlap
                    overlap_length = 0
                    overlap_sentences = []
                    
                    for prev_sent in reversed(current_chunk):
                        if overlap_length + len(prev_sent) <= self.chunk_overlap:
                            overlap_sentences.insert(0, prev_sent)
                            overlap_length += len(prev_sent) + 1  # +1 for the space
                        else:
                            break
                    
                    current_chunk = overlap_sentences
                    current_length = overlap_length
                else:
                    current_chunk = []
                    current_length = 0
            
            # Add the sentence to the current chunk
            current_chunk.append(sentence)
            current_length += sentence_len + 1  # +1 for space
        
        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _chunk_fixed(self, text: str) -> List[str]:
        """
        Chunk by fixed size with overlap
        
        Args:
            text: Text to chunk
            
        Returns:
            List of chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            # Add the chunk
            chunks.append(text[start:end])
            
            # Move start position for next chunk, considering overlap
            start = end - self.chunk_overlap
            
            # Avoid getting stuck
            if start >= end:
                start = end
        
        return chunks
