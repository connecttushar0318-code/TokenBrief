import re
from typing import List, Dict, Any

class DocumentTextChunker:
    @staticmethod
    def chunk_page_text(
        text: str,
        filename: str,
        page_number: int,
        chunk_size: int = 1200,
        overlap_words_count: int = 35
    ) -> List[Dict[str, Any]]:
        clean_text = re.sub(r"\s+", " ", text).strip()
        if not clean_text:
            return []
        words = clean_text.split(" ")
        chunks = []
        current_chunk_words = []
        current_len = 0
        for word in words:
            if not word:
                continue
            current_chunk_words.append(word)
            current_len += len(word) + 1
            if current_len >= chunk_size:
                chunk_str = " ".join(current_chunk_words)
                chunks.append({
                    "filename": filename,
                    "page_number": page_number,
                    "chunk_text": f"[Document: {filename} | Page: {page_number}]\n{chunk_str}"
                })
                current_chunk_words = current_chunk_words[-overlap_words_count:]
                current_len = sum(len(w) + 1 for w in current_chunk_words)
        if current_chunk_words:
            chunk_str = " ".join(current_chunk_words)
            chunks.append({
                "filename": filename,
                "page_number": page_number,
                "chunk_text": f"[Document: {filename} | Page: {page_number}]\n{chunk_str}"
            })
        return chunks

    @classmethod
    def split_pages_into_chunks(
        cls,
        extracted_pages: List[Dict[str, Any]],
        document_filename: str = "document.pdf",
        target_chunk_size: int = 1200,
        chunk_overlap_size: int = 200
    ) -> List[Dict[str, Any]]:
        generated_chunks_list = []
        global_chunk_counter = 0
        for single_page in extracted_pages:
            page_text = single_page.get("text_content", "").strip()
            page_number = single_page.get("page_number", 1)
            page_chunks = cls.chunk_page_text(
                text=page_text,
                filename=document_filename,
                page_number=page_number,
                chunk_size=target_chunk_size
            )
            for chunk_data in page_chunks:
                chunk_data["chunk_index"] = global_chunk_counter
                generated_chunks_list.append(chunk_data)
                global_chunk_counter += 1
        return generated_chunks_list
