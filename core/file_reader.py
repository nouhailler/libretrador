"""Lecture de fichiers .txt, .docx et .pdf en liste de paragraphes."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def read_txt(path: Path) -> list[str]:
    """Lit un fichier texte et le découpe en paragraphes."""
    text = path.read_text(encoding="utf-8", errors="replace")
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs if paragraphs else [text.strip()]


def read_docx(path: Path) -> list[str]:
    """Lit un fichier .docx et retourne une liste de paragraphes non vides."""
    try:
        from docx import Document
    except ImportError:
        raise RuntimeError(
            "python-docx n'est pas installé.\n"
            "Installez-le avec : pip install python-docx"
        )
    doc = Document(str(path))
    return [p.text.strip() for p in doc.paragraphs if p.text.strip()]


def read_pdf(path: Path) -> list[str]:
    """Lit un fichier .pdf texte et retourne une liste de paragraphes."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError(
            "pypdf n'est pas installé.\n"
            "Installez-le avec : pip install pypdf"
        )
    reader = PdfReader(str(path))
    paragraphs = []
    for page in reader.pages:
        text = page.extract_text() or ""
        for block in text.split("\n\n"):
            block = block.strip()
            if block:
                paragraphs.append(block)
    return paragraphs


def read_file(path: Path) -> list[str]:
    """Dispatche vers le bon lecteur selon l'extension."""
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return read_txt(path)
    elif suffix == ".docx":
        return read_docx(path)
    elif suffix == ".pdf":
        return read_pdf(path)
    else:
        raise ValueError(f"Format non supporté : {suffix!r}")
