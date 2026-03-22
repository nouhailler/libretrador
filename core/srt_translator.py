"""Parsing, reconstruction et chunking des fichiers SRT."""

import re
from dataclasses import dataclass
from typing import Generator

_SEPARATOR = "\n§§§\n"


@dataclass
class SrtBlock:
    index: str     # "1", "2", etc.
    timecode: str  # "00:00:01,000 --> 00:00:03,500"
    text: str      # texte à traduire (peut être multiligne)


def parse_srt(content: str) -> list[SrtBlock]:
    """
    Parse un fichier .srt en blocs structurés.
    Robuste aux variations : BOM, \\r\\n, lignes vides multiples.
    """
    content = content.strip().replace("\r\n", "\n").replace("\r", "\n")
    content = content.lstrip("\ufeff")  # Supprimer BOM éventuel

    blocks: list[SrtBlock] = []
    pattern = re.compile(
        r"(\d+)\n"                          # index
        r"(\d{2}:\d{2}:\d{2},\d{3}"        # timecode début
        r"\s*-->\s*"                         # séparateur
        r"\d{2}:\d{2}:\d{2},\d{3})"        # timecode fin
        r"\n([\s\S]*?)(?=\n\n\d+\n|\Z)",    # texte multiligne
        re.MULTILINE,
    )
    for m in pattern.finditer(content):
        text = m.group(3).strip()
        if text:  # ignorer les blocs vides
            blocks.append(SrtBlock(
                index=m.group(1),
                timecode=m.group(2),
                text=text,
            ))
    return blocks


def blocks_to_srt(blocks: list[SrtBlock]) -> str:
    """Reconstruit le contenu d'un fichier .srt depuis les blocs traduits."""
    parts = [f"{b.index}\n{b.timecode}\n{b.text}" for b in blocks]
    return "\n\n".join(parts) + "\n"


def chunk_blocks(
    blocks: list[SrtBlock],
    max_chars: int = 1500,
) -> Generator[tuple[list[SrtBlock], str], None, None]:
    """
    Regroupe les blocs en chunks pour limiter les appels au moteur.
    Chaque chunk contient plusieurs blocs dont le texte combiné
    ne dépasse pas max_chars.
    Séparateur interne : "\\n§§§\\n" (marqueur interne non visible dans .srt).
    """
    chunk_texts: list[str] = []
    chunk_block_list: list[SrtBlock] = []
    count = 0

    for block in blocks:
        if count + len(block.text) > max_chars and chunk_texts:
            yield chunk_block_list, _SEPARATOR.join(chunk_texts)
            chunk_texts, chunk_block_list, count = [], [], 0
        chunk_texts.append(block.text)
        chunk_block_list.append(block)
        count += len(block.text)

    if chunk_texts:
        yield chunk_block_list, _SEPARATOR.join(chunk_texts)


def srt_preview(blocks: list[SrtBlock], n: int = 3) -> str:
    """Retourne un aperçu lisible des n premiers blocs."""
    lines = []
    for b in blocks[:n]:
        lines.append(f"[{b.index}] {b.timecode}\n{b.text}")
    if len(blocks) > n:
        lines.append(f"[… {len(blocks) - n} blocs supplémentaires]")
    return "\n\n".join(lines)
