#!/usr/bin/env python3
"""
Script utilitaire pour générer les PNG depuis le SVG source.
Nécessite : sudo apt install librsvg2-bin
Usage    : python3 assets/generate_icons.py
"""
import subprocess
from pathlib import Path

SVG = Path(__file__).parent / "libretrador.svg"
SIZES = [16, 32, 48, 128]

for size in SIZES:
    out = SVG.parent / f"libretrador_{size}.png"
    subprocess.run(
        ["rsvg-convert", "-w", str(size), "-h", str(size), str(SVG), "-o", str(out)],
        check=True,
    )
    print(f"Généré : {out}")
