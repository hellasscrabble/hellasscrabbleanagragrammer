"""Build a single-file, offline HTML copy that opens directly from disk."""

from __future__ import annotations

import base64
import json
from pathlib import Path
import re


SITE = Path(__file__).resolve().parent
PROJECT = SITE.parent
OUTPUT = PROJECT / "hellasscrabbleanagrammer-standalone.html"


def data_uri(path: Path, mime: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def main() -> None:
    tsv_path = SITE / "data" / "words.tsv"
    if not tsv_path.exists():
        raise FileNotFoundError("Δεν βρέθηκε το λεξικό. Τρέξε πρώτα: python site/build_dictionary.py")

    entries = []
    with tsv_path.open("r", encoding="utf-8") as source:
        for line in source:
            line = line.rstrip("\r\n")
            if not line:
                continue
            word, separator, meaning = line.partition("\t")
            entries.append([word, meaning if separator else ""])
    dictionary_json = json.dumps(entries, ensure_ascii=False, separators=(",", ":"))
    dictionary_json = dictionary_json.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

    html = (SITE / "index.html").read_text(encoding="utf-8")
    css = (SITE / "styles.css").read_text(encoding="utf-8")
    js = (SITE / "app.js").read_text(encoding="utf-8")
    html = re.sub(r'\s*<link rel="manifest"[^>]*>', "", html)
    html = re.sub(r'\s*<link rel="icon"[^>]*>', "", html)
    html = html.replace('<link rel="stylesheet" href="./styles.css">', f"<style>\n{css}\n</style>")
    html = html.replace(
        './assets/ela-scrabble-logo.png',
        data_uri(SITE / "assets" / "ela-scrabble-logo.png", "image/png"),
    )
    html = html.replace(
        './assets/oi-lekseis-2-8-grammaton-scrabble.jpg',
        data_uri(SITE / "assets" / "oi-lekseis-2-8-grammaton-scrabble.jpg", "image/jpeg"),
    )
    html = html.replace(
        '<script src="./app.js" defer></script>',
        '<script id="embedded-dictionary" type="application/json">'
        + dictionary_json
        + '</script>\n<script>\n'
        + js.replace("</script", "<\\/script")
        + "\n</script>",
    )
    OUTPUT.write_text(html, encoding="utf-8", newline="\n")
    print(f"Δημιουργήθηκε {OUTPUT} ({OUTPUT.stat().st_size:,} bytes, {len(entries):,} λέξεις).")


if __name__ == "__main__":
    main()
