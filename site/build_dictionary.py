"""Convert the supplied Excel list into the compact browser dictionary TSV."""

from __future__ import annotations

import unicodedata
from pathlib import Path
import shutil

from openpyxl import load_workbook
from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "ΒΑΣΗΛΕΞΕΩΝ (1).xlsx"
OUTPUT = Path(__file__).resolve().parent / "data" / "words.tsv"
ASSETS = Path(__file__).resolve().parent / "assets"


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.strip().upper())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Δεν βρέθηκε το αρχείο λεξικού: {SOURCE}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    workbook = load_workbook(SOURCE, read_only=True, data_only=True)
    sheet = workbook.worksheets[0]
    entries: dict[str, str] = {}
    try:
        for raw_word, raw_meaning in sheet.iter_rows(min_col=1, max_col=2, values_only=True):
            if not isinstance(raw_word, str):
                continue
            word = normalize(raw_word)
            if not word or not word.isalpha():
                continue
            meaning = raw_meaning.strip() if isinstance(raw_meaning, str) else ""
            meaning = meaning.replace("\t", " ").replace("\r", " ").replace("\n", " ")
            if word not in entries or meaning:
                entries[word] = meaning
    finally:
        workbook.close()

    with OUTPUT.open("w", encoding="utf-8", newline="\n") as output:
        for word in sorted(entries):
            output.write(f"{word}\t{entries[word]}\n")
    build_assets()
    print(f"Δημιουργήθηκε {OUTPUT} με {len(entries):,} λέξεις.")


def build_assets() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "ΕΛΑ ΣΚΡΑΜΠΛ LOGO.png", ASSETS / "ela-scrabble-logo.png")
    shutil.copy2(ROOT / "oi-lekseis-2-8-grammaton-scrabble.jpg", ASSETS / "oi-lekseis-2-8-grammaton-scrabble.jpg")

    logo = Image.open(ROOT / "ΕΛΑ ΣΚΡΑΜΠΛ LOGO.png").convert("RGBA")
    for size in (192, 512):
        icon = Image.new("RGBA", (size, size), "#eaf4fc")
        mark = logo.copy()
        mark.thumbnail((int(size * 0.88), int(size * 0.88)), Image.Resampling.LANCZOS)
        icon.alpha_composite(mark, ((size - mark.width) // 2, (size - mark.height) // 2))
        icon.convert("RGB").save(ASSETS / f"icon-{size}.png", optimize=True)


if __name__ == "__main__":
    main()
