"""
File parsing utilities for the Graphiti CLI.
Handles extraction of text from various file formats.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple
import tiktoken

try:
    import PyPDF2
    from docx import Document
    from openpyxl import load_workbook
    import markdown
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Run: pip install -r requirements.txt")
    raise


class FileParser:
    """Base class for file parsing with chunking support."""

    def __init__(self, max_tokens: int = 1500, overlap_tokens: int = 200):
        """
        Initialize the file parser.

        Args:
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Overlap between chunks
        """
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        return len(self.encoding.encode(text))

    def chunk_text(self, text: str) -> List[str]:
        """
        Chunk text into smaller pieces with overlap.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        # Split by paragraphs first
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        chunks = []
        current_chunk = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self.count_tokens(para)

            # If single paragraph exceeds max tokens, split it further
            if para_tokens > self.max_tokens:
                # Save current chunk if any
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_tokens = 0

                # Split long paragraph by sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sent in sentences:
                    sent_tokens = self.count_tokens(sent)
                    if current_tokens + sent_tokens > self.max_tokens:
                        if current_chunk:
                            chunks.append(' '.join(current_chunk))
                        current_chunk = [sent]
                        current_tokens = sent_tokens
                    else:
                        current_chunk.append(sent)
                        current_tokens += sent_tokens

            # Normal paragraph handling
            elif current_tokens + para_tokens > self.max_tokens:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_tokens = para_tokens
            else:
                current_chunk.append(para)
                current_tokens += para_tokens

        # Add final chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    def detect_sections(self, text: str) -> List[Tuple[str, str]]:
        """
        Detect sections in text based on headers.

        Args:
            text: Full text content

        Returns:
            List of (section_name, section_content) tuples
        """
        # Common header patterns
        header_patterns = [
            r'^#{1,3}\s+(.+)$',  # Markdown headers
            r'^([A-Z][A-Z\s]{5,})$',  # ALL CAPS headers
            r'^\d+\.\s+([A-Z].+)$',  # Numbered headers like "1. Introduction"
        ]

        sections = []
        current_section = "Introduction"
        current_content = []

        lines = text.split('\n')

        for line in lines:
            is_header = False

            for pattern in header_patterns:
                match = re.match(pattern, line.strip())
                if match:
                    # Save previous section
                    if current_content:
                        sections.append((current_section, '\n'.join(current_content)))

                    # Start new section
                    current_section = match.group(1).strip()
                    current_content = []
                    is_header = True
                    break

            if not is_header:
                current_content.append(line)

        # Add final section
        if current_content:
            sections.append((current_section, '\n'.join(current_content)))

        return sections if len(sections) > 1 else []


class PDFParser(FileParser):
    """Parser for PDF files."""

    def parse(self, file_path: str) -> Tuple[str, List[Tuple[str, str]]]:
        """
        Parse PDF file.

        Returns:
            (full_text, sections) where sections is list of (name, content) tuples
        """
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""

            for page in reader.pages:
                text += page.extract_text() + "\n\n"

        # Detect sections
        sections = self.detect_sections(text)

        return text.strip(), sections


class DOCXParser(FileParser):
    """Parser for DOCX files."""

    def parse(self, file_path: str) -> Tuple[str, List[Tuple[str, str]]]:
        """
        Parse DOCX file.

        Returns:
            (full_text, sections) where sections is list of (name, content) tuples
        """
        doc = Document(file_path)

        paragraphs = []
        sections = []
        current_section = None
        current_content = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # Check if this is a heading
            if para.style.name.startswith('Heading'):
                if current_section and current_content:
                    sections.append((current_section, '\n\n'.join(current_content)))
                current_section = text
                current_content = []
            else:
                paragraphs.append(text)
                if current_section is not None:
                    current_content.append(text)

        # Add final section
        if current_section and current_content:
            sections.append((current_section, '\n\n'.join(current_content)))

        full_text = '\n\n'.join(paragraphs)

        # If no sections found via headings, try pattern detection
        if not sections:
            sections = self.detect_sections(full_text)

        return full_text, sections


class ExcelParser(FileParser):
    """Parser for Excel files."""

    def parse(self, file_path: str) -> Tuple[str, List[Tuple[str, str]]]:
        """
        Parse Excel file.

        Returns:
            (full_text, sections) where each sheet is a section
        """
        workbook = load_workbook(file_path, data_only=True)

        sections = []
        all_text = []

        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            sheet_text = []

            for row in sheet.iter_rows(values_only=True):
                row_text = '\t'.join([str(cell) if cell is not None else '' for cell in row])
                if row_text.strip():
                    sheet_text.append(row_text)

            content = '\n'.join(sheet_text)
            if content.strip():
                sections.append((sheet_name, content))
                all_text.append(f"[Sheet: {sheet_name}]\n{content}")

        return '\n\n'.join(all_text), sections


class TextParser(FileParser):
    """Parser for plain text and markdown files."""

    def parse(self, file_path: str) -> Tuple[str, List[Tuple[str, str]]]:
        """
        Parse text file.

        Returns:
            (full_text, sections)
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Detect sections
        sections = self.detect_sections(text)

        return text.strip(), sections


def get_parser(file_path: str) -> FileParser:
    """
    Get appropriate parser based on file extension.

    Args:
        file_path: Path to the file

    Returns:
        Parser instance

    Raises:
        ValueError: If file type is not supported
    """
    ext = Path(file_path).suffix.lower()

    if ext == '.pdf':
        return PDFParser()
    elif ext in ['.docx', '.doc']:
        return DOCXParser()
    elif ext in ['.xlsx', '.xls']:
        return ExcelParser()
    elif ext in ['.txt', '.md']:
        return TextParser()
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def parse_file(file_path: str) -> Dict:
    """
    Parse a file and extract its content with metadata.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with:
            - full_text: Complete file content
            - sections: List of (section_name, section_content) tuples
            - word_count: Approximate word count
            - token_count: Approximate token count
            - has_sections: Whether sections were detected
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    parser = get_parser(file_path)
    full_text, sections = parser.parse(file_path)

    return {
        'full_text': full_text,
        'sections': sections,
        'word_count': len(full_text.split()),
        'token_count': parser.count_tokens(full_text),
        'has_sections': len(sections) > 0,
        'parser': parser,  # Keep parser for chunking if needed
    }
