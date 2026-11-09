import re
from typing import List, Dict, Any

class DocumentTextChunker:
    @staticmethod
    def split_pages_into_chunks(
        extracted_pages: List[Dict[str, Any]],
        target_chunk_size: int = 500,
        chunk_overlap_size: int = 100
    ) -> List[Dict[str, Any]]:
        generated_chunks_list = []
        global_chunk_counter = 0

        for single_page in extracted_pages:
            page_text = single_page["text_content"].strip()
            page_number = single_page["page_number"]

            if not page_text:
                continue

            paragraphs = [p.strip() for p in page_text.split("\n") if p.strip()]
            if not paragraphs:
                paragraphs = [page_text]

            current_chunk_words = []
            current_length = 0

            words_stream = []
            for paragraph in paragraphs:
                paragraph_words = paragraph.split(" ")
                words_stream.extend([w for w in paragraph_words if w])

            index = 0
            total_words = len(words_stream)

            while index < total_words:
                chunk_words = []
                chunk_char_count = 0

                while index < total_words and chunk_char_count < target_chunk_size:
                    word = words_stream[index]
                    chunk_words.append(word)
                    chunk_char_count += len(word) + 1
                    index += 1

                joined_text = " ".join(chunk_words).strip()
                if joined_text:
                    generated_chunks_list.append({
                        "chunk_index": global_chunk_counter,
                        "page_number": page_number,
                        "chunk_text": joined_text
                    })
                    global_chunk_counter += 1

                if index < total_words:
                    overlap_chars = 0
                    rewind_count = 0
                    for word in reversed(chunk_words):
                        overlap_chars += len(word) + 1
                        rewind_count += 1
                        if overlap_chars >= chunk_overlap_size:
                            break
                    index = max(index - rewind_count, index - len(chunk_words) + 1)

        return generated_chunks_list
