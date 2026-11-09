import re
from typing import List, Dict, Any, Optional

class DocumentTextChunker:

    @classmethod
    def _detect_dominant_section(cls, text: str) -> str:
        heading_matches = re.findall(
            r"(?:^|\n)(?:#{1,4}\s+([^\n\r]+)|(?:Module|Unit|Chapter|Section)\s*[\d:]+[^\n\r]*|([A-Z\s]{4,35})(?=\n|$))",
            text
        )
        for h_tuple in heading_matches:
            heading = next((item.strip() for item in h_tuple if item and len(item.strip()) > 3), None)
            if heading and not heading.lower().startswith("page"):
                return heading[:50]
        return "Core Content"

    @classmethod
    def chunk_page_text(
        cls,
        text: str,
        filename: str,
        page_number: int,
        chunk_size: int = 1200,
        overlap_words_count: int = 35
    ) -> List[Dict[str, Any]]:
        raw_lines = text.split("\n")
        detected_section = cls._detect_dominant_section(text)

        blocks = []
        current_table = []

        for line in raw_lines:
            stripped_line = line.strip()
            if stripped_line.startswith("|") and stripped_line.endswith("|"):
                current_table.append(stripped_line)
            else:
                if current_table:
                    blocks.append("\n".join(current_table))
                    current_table = []
                if stripped_line:
                    blocks.append(stripped_line)

        if current_table:
            blocks.append("\n".join(current_table))

        chunks = []
        current_chunk_blocks = []
        current_len = 0

        header_prefix = f"[Doc: {filename} | Section: {detected_section} | Page: {page_number}]"

        for block in blocks:
            block_len = len(block) + 1
            if current_len + block_len > chunk_size and current_chunk_blocks:
                chunk_body = "\n".join(current_chunk_blocks).strip()
                chunks.append({
                    "filename": filename,
                    "page_number": page_number,
                    "section": detected_section,
                    "chunk_text": f"{header_prefix}\n{chunk_body}"
                })

                last_block_words = current_chunk_blocks[-1].split()
                overlap_text = " ".join(last_block_words[-overlap_words_count:]) if len(last_block_words) > overlap_words_count else current_chunk_blocks[-1]
                current_chunk_blocks = [overlap_text, block]
                current_len = len(overlap_text) + block_len + 2
            else:
                current_chunk_blocks.append(block)
                current_len += block_len

        if current_chunk_blocks:
            chunk_body = "\n".join(current_chunk_blocks).strip()
            chunks.append({
                "filename": filename,
                "page_number": page_number,
                "section": detected_section,
                "chunk_text": f"{header_prefix}\n{chunk_body}"
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
