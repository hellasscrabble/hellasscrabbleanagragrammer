"""Serve the local PWA and open it in the default browser."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
import webbrowser


SITE_DIR = Path(__file__).resolve().parent / "site"
URL = "http://127.0.0.1:8000/"


def main() -> None:
    if not (SITE_DIR / "data" / "words.tsv").exists():
        raise FileNotFoundError("Δεν βρέθηκε το λεξικό. Τρέξε πρώτα: python site/build_dictionary.py")
    os.chdir(SITE_DIR)
    server = ThreadingHTTPServer(("127.0.0.1", 8000), SimpleHTTPRequestHandler)
    print(f"Η προεπισκόπηση είναι διαθέσιμη στο {URL}")
    print("Άφησε αυτό το παράθυρο ανοιχτό. Για τερματισμό πάτησε Ctrl+C.")
    webbrowser.open(URL)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nΟ τοπικός server τερματίστηκε.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
