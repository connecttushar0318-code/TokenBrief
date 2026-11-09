from typing import List, Dict, Any
from pathlib import Path
from pypdf import PdfReader

class PDFTextExtractor:
    @staticmethod
    def extract_text_from_file(file_path: str) -> List[Dict[str, Any]]:
        target_path = Path(file_path)
        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_extension = target_path.suffix.lower()

        if file_extension in (".txt", ".md"):
            with open(target_path, "r", encoding="utf-8", errors="ignore") as stream:
                full_text = stream.read()

            clean_text = " ".join(full_text.split())
            if not clean_text:
                return []

            paragraphs = full_text.split("\n\n")
            pages = []
            current_page_text = []
            current_length = 0
            page_counter = 1

            for p in paragraphs:
                trimmed = p.strip()
                if not trimmed:
                    continue
                current_page_text.append(trimmed)
                current_length += len(trimmed)
                if current_length > 2500:
                    pages.append({
                        "page_number": page_counter,
                        "text_content": "\n\n".join(current_page_text)
                    })
                    page_counter += 1
                    current_page_text = []
                    current_length = 0

            if current_page_text:
                pages.append({
                    "page_number": page_counter,
                    "text_content": "\n\n".join(current_page_text)
                })

            return pages

        pdf_reader = PdfReader(str(target_path))
        extracted_pages_list = []
        page_number = 1

        for pdf_page in pdf_reader.pages:
            raw_text = pdf_page.extract_text() or ""
            clean_text = " ".join(raw_text.split())
            if clean_text:
                extracted_pages_list.append({
                    "page_number": page_number,
                    "text_content": clean_text
                })
            page_number += 1

        return extracted_pages_list

    @classmethod
    def extract_text_from_pdf(cls, pdf_file_path: str) -> List[Dict[str, Any]]:
        return cls.extract_text_from_file(pdf_file_path)
