"""
FormSaathi - PDF Extraction Module
Extracts readable text, page structure, and document metrics using PyMuPDF (fitz)
with seamless fallback to PyPDF2 if PyMuPDF is not installed.
Provides automatic detection of scanned/empty documents and context-length guards.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union
import io

# Try importing fitz (PyMuPDF), fallback to PyPDF2 if not available
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    try:
        import PyPDF2
        HAS_PYPDF2 = True
    except ImportError:
        HAS_PYPDF2 = False


@dataclass
class ExtractedDocument:
    full_text: str
    page_count: int
    total_chars: int
    total_words: int
    is_scanned_or_empty: bool = False
    is_truncated: bool = False
    truncation_note: str = ""
    extractor_engine: str = "PyMuPDF"
    pages: List[Dict[str, Union[int, str]]] = field(default_factory=list)
    error_message: Optional[str] = None


# Safe character threshold for LLM context window (~15,000 words / ~50,000 chars)
MAX_CHAR_THRESHOLD = 50000
MIN_READABLE_CHARS = 40


def extract_text_from_pdf(
    file_source: Union[bytes, io.BytesIO, str],
    max_chars: int = MAX_CHAR_THRESHOLD,
) -> ExtractedDocument:
    """
    Extracts text and metadata from a PDF file stream or file path.

    Args:
        file_source: File bytes, BytesIO buffer (e.g. from Streamlit file uploader), or filepath.
        max_chars: Upper character limit to prevent context overflow while alerting user.

    Returns:
        ExtractedDocument instance with extracted text, stats, and status flags.
    """
    if not HAS_PYMUPDF and not HAS_PYPDF2:
        return ExtractedDocument(
            full_text="",
            page_count=0,
            total_chars=0,
            total_words=0,
            is_scanned_or_empty=True,
            error_message="Neither PyMuPDF nor PyPDF2 is installed on the system.",
        )

    # Convert file_source to raw bytes if needed
    try:
        raw_bytes: bytes
        if isinstance(file_source, bytes):
            raw_bytes = file_source
        elif isinstance(file_source, (io.BytesIO, io.BufferedReader)):
            raw_bytes = file_source.read()
        elif isinstance(file_source, str):
            with open(file_source, "rb") as f:
                raw_bytes = f.read()
        elif hasattr(file_source, "getvalue"):
            raw_bytes = file_source.getvalue()
        elif hasattr(file_source, "read"):
            raw_bytes = file_source.read()
        else:
            return ExtractedDocument(
                full_text="",
                page_count=0,
                total_chars=0,
                total_words=0,
                is_scanned_or_empty=True,
                error_message="Unsupported input format for PDF extraction.",
            )

        if len(raw_bytes) == 0:
            return ExtractedDocument(
                full_text="",
                page_count=0,
                total_chars=0,
                total_words=0,
                is_scanned_or_empty=True,
                error_message="Uploaded PDF file is completely empty (0 bytes).",
            )

        # 1. Primary Engine: PyMuPDF (fitz)
        if HAS_PYMUPDF:
            return _extract_with_pymupdf(raw_bytes, max_chars)

        # 2. Fallback Engine: PyPDF2
        return _extract_with_pypdf2(raw_bytes, max_chars)

    except Exception as exc:
        return ExtractedDocument(
            full_text="",
            page_count=0,
            total_chars=0,
            total_words=0,
            is_scanned_or_empty=True,
            error_message=f"Error reading PDF: {str(exc)}",
        )


def _extract_with_pymupdf(raw_bytes: bytes, max_chars: int) -> ExtractedDocument:
    doc = fitz.open(stream=raw_bytes, filetype="pdf")
    page_count = len(doc)
    if page_count == 0:
        doc.close()
        return ExtractedDocument(
            full_text="",
            page_count=0,
            total_chars=0,
            total_words=0,
            is_scanned_or_empty=True,
            extractor_engine="PyMuPDF",
            error_message="The uploaded PDF contains zero pages.",
        )

    pages_data = []
    full_text_parts = []
    running_char_count = 0
    is_truncated = False
    truncation_note = ""
    included_pages = 0

    for page_idx in range(page_count):
        page = doc[page_idx]
        page_text = page.get_text("text").strip()
        formatted_page_block = f"--- [PAGE {page_idx + 1} OF {page_count}] ---\n{page_text}\n"
        block_len = len(formatted_page_block)

        if running_char_count + block_len > max_chars:
            is_truncated = True
            if included_pages > 0:
                truncation_note = (
                    f"Notice: Document is long ({page_count} pages). FormSaathi analyzed "
                    f"the first {included_pages} page(s) ({running_char_count:,} characters) "
                    f"to stay within the AI processing window. Content beyond page {included_pages} "
                    f"was not analyzed."
                )
                break
            else:
                # Truncate first page content if even page 1 exceeds limit
                truncated_text = page_text[:max_chars]
                formatted_page_block = f"--- [PAGE 1 OF {page_count} (TRUNCATED)] ---\n{truncated_text}\n"
                full_text_parts.append(formatted_page_block)
                pages_data.append({
                    "page_number": 1,
                    "text": truncated_text,
                    "char_count": len(truncated_text),
                    "word_count": len(truncated_text.split()),
                })
                truncation_note = (
                    f"Notice: Document is long. FormSaathi analyzed the first "
                    f"{len(truncated_text):,} characters of page 1 to stay within the AI processing window."
                )
                included_pages = 1
                break

        full_text_parts.append(formatted_page_block)
        pages_data.append({
            "page_number": page_idx + 1,
            "text": page_text,
            "char_count": len(page_text),
            "word_count": len(page_text.split()),
        })
        running_char_count += block_len
        included_pages += 1

    doc.close()

    combined_text = "\n".join(full_text_parts).strip()
    total_chars = sum(p["char_count"] for p in pages_data)
    total_words = sum(p["word_count"] for p in pages_data)

    if total_chars < MIN_READABLE_CHARS:
        return ExtractedDocument(
            full_text=combined_text,
            page_count=page_count,
            total_chars=total_chars,
            total_words=total_words,
            is_scanned_or_empty=True,
            extractor_engine="PyMuPDF",
            pages=pages_data,
            error_message=(
                "Scanned or image-only document detected: We could not find selectable text "
                f"in this PDF (only {total_chars} characters extracted). "
                "FormSaathi requires a PDF with selectable text. "
                "Please upload a digitally generated PDF or one with an OCR text layer."
            ),
        )

    return ExtractedDocument(
        full_text=combined_text,
        page_count=page_count,
        total_chars=total_chars,
        total_words=total_words,
        is_scanned_or_empty=False,
        is_truncated=is_truncated,
        truncation_note=truncation_note,
        extractor_engine="PyMuPDF",
        pages=pages_data,
    )


def _extract_with_pypdf2(raw_bytes: bytes, max_chars: int) -> ExtractedDocument:
    reader = PyPDF2.PdfReader(io.BytesIO(raw_bytes))
    page_count = len(reader.pages)
    if page_count == 0:
        return ExtractedDocument(
            full_text="",
            page_count=0,
            total_chars=0,
            total_words=0,
            is_scanned_or_empty=True,
            extractor_engine="PyPDF2 (Fallback)",
            error_message="The uploaded PDF contains zero pages.",
        )

    pages_data = []
    full_text_parts = []
    running_char_count = 0
    is_truncated = False
    truncation_note = ""
    included_pages = 0

    for page_idx in range(page_count):
        page = reader.pages[page_idx]
        page_text = (page.extract_text() or "").strip()
        formatted_page_block = f"--- [PAGE {page_idx + 1} OF {page_count}] ---\n{page_text}\n"
        block_len = len(formatted_page_block)

        if running_char_count + block_len > max_chars:
            is_truncated = True
            if included_pages > 0:
                truncation_note = (
                    f"Notice: Document is long ({page_count} pages). FormSaathi analyzed "
                    f"the first {included_pages} page(s) ({running_char_count:,} characters) "
                    f"to stay within the AI processing window. Content beyond page {included_pages} "
                    f"was not analyzed."
                )
                break
            else:
                # Truncate first page content if even page 1 exceeds limit
                truncated_text = page_text[:max_chars]
                formatted_page_block = f"--- [PAGE 1 OF {page_count} (TRUNCATED)] ---\n{truncated_text}\n"
                full_text_parts.append(formatted_page_block)
                pages_data.append({
                    "page_number": 1,
                    "text": truncated_text,
                    "char_count": len(truncated_text),
                    "word_count": len(truncated_text.split()),
                })
                truncation_note = (
                    f"Notice: Document is long. FormSaathi analyzed the first "
                    f"{len(truncated_text):,} characters of page 1 to stay within the AI processing window."
                )
                included_pages = 1
                break

        full_text_parts.append(formatted_page_block)
        pages_data.append({
            "page_number": page_idx + 1,
            "text": page_text,
            "char_count": len(page_text),
            "word_count": len(page_text.split()),
        })
        running_char_count += block_len
        included_pages += 1

    combined_text = "\n".join(full_text_parts).strip()
    total_chars = sum(p["char_count"] for p in pages_data)
    total_words = sum(p["word_count"] for p in pages_data)

    if total_chars < MIN_READABLE_CHARS:
        return ExtractedDocument(
            full_text=combined_text,
            page_count=page_count,
            total_chars=total_chars,
            total_words=total_words,
            is_scanned_or_empty=True,
            extractor_engine="PyPDF2 (Fallback)",
            pages=pages_data,
            error_message=(
                "Scanned or image-only document detected: We could not find selectable text "
                f"in this PDF (only {total_chars} characters extracted). "
                "FormSaathi requires a PDF with selectable text. "
                "Please upload a digitally generated PDF or one with an OCR text layer."
            ),
        )

    return ExtractedDocument(
        full_text=combined_text,
        page_count=page_count,
        total_chars=total_chars,
        total_words=total_words,
        is_scanned_or_empty=False,
        is_truncated=is_truncated,
        truncation_note=truncation_note,
        extractor_engine="PyPDF2 (Fallback)",
        pages=pages_data,
    )
