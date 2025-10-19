"""
Simplified File Parsing Utilities

Extract text from various file formats without complex chunking or section detection.
Let Graphiti handle the heavy lifting.
"""

import os
from pathlib import Path
from typing import Dict

try:
    import PyPDF2
    from docx import Document
    from openpyxl import load_workbook
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Run: pip install PyPDF2 python-docx openpyxl")
    raise


def parse_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.

    Args:
        file_path: Path to the PDF file

    Returns:
        Extracted text content
    """
    text = []

    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)

    return '\n\n'.join(text)


def parse_docx(file_path: str) -> str:
    """
    Extract text from a DOCX file.

    Args:
        file_path: Path to the DOCX file

    Returns:
        Extracted text content
    """
    doc = Document(file_path)
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return '\n\n'.join(paragraphs)


def parse_excel(file_path: str) -> str:
    """
    Extract text from an Excel file.

    Args:
        file_path: Path to the Excel file

    Returns:
        Extracted text content
    """
    workbook = load_workbook(file_path, data_only=True)
    sheets_content = []

    for sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]

        # Sheet header
        sheets_content.append(f"=== {sheet_name} ===\n")

        # Extract all rows
        rows = []
        for row in sheet.iter_rows(values_only=True):
            # Filter out completely empty rows
            if any(cell is not None for cell in row):
                row_text = '\t'.join(str(cell) if cell is not None else '' for cell in row)
                rows.append(row_text)

        sheets_content.append('\n'.join(rows))

    return '\n\n'.join(sheets_content)


def parse_text(file_path: str) -> str:
    """
    Read a text file (TXT, MD, etc.).

    Args:
        file_path: Path to the text file

    Returns:
        File contents
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def parse_file(file_path: str) -> Dict[str, str]:
    """
    Parse a file and extract its text content.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with 'content' and 'filename'

    Raises:
        ValueError: If file type is not supported
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get file extension
    extension = path.suffix.lower()

    # Parse based on file type
    if extension == '.pdf':
        content = parse_pdf(file_path)
    elif extension == '.docx':
        content = parse_docx(file_path)
    elif extension in ['.xlsx', '.xls']:
        content = parse_excel(file_path)
    elif extension in ['.txt', '.md']:
        content = parse_text(file_path)
    else:
        raise ValueError(f"Unsupported file type: {extension}")

    return {
        'content': content,
        'filename': path.name,
        'extension': extension,
    }
