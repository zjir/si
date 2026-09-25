"""Pomocný skript kola 1: extrakce textu z popisu P.A.T. pro cílené čtení (výstup jen do složky kola)."""
import importlib
import sys
from pathlib import Path

SRC = Path("PAT/Popis OS P.A.T.pdf")
OUT = Path("runs/TASK-0001/round-01/pat_text.txt")


def with_pypdf():
    from pypdf import PdfReader

    r = PdfReader(str(SRC))
    parts = []
    for i, p in enumerate(r.pages, 1):
        parts.append(f"\n===== STRANA {i} =====\n")
        parts.append(p.extract_text() or "")
    return "".join(parts), len(r.pages)


def with_fitz():
    import fitz

    d = fitz.open(str(SRC))
    parts = []
    for i, p in enumerate(d, 1):
        parts.append(f"\n===== STRANA {i} =====\n")
        parts.append(p.get_text())
    return "".join(parts), len(d)


def with_pdfminer():
    from pdfminer.high_level import extract_text

    t = extract_text(str(SRC))
    return t, t.count("\f")


for name, fn in [("fitz", with_fitz), ("pypdf", with_pypdf), ("pdfminer", with_pdfminer)]:
    try:
        importlib.import_module(name if name != "pdfminer" else "pdfminer.high_level")
    except Exception:
        print("chybí", name)
        continue
    try:
        text, n = fn()
        OUT.write_text(text, encoding="utf-8")
        print("OK", name, "stran:", n, "znaků:", len(text))
        sys.exit(0)
    except Exception as e:
        print("selhal", name, e)

print("žádná knihovna pro PDF není dostupná")
sys.exit(1)
