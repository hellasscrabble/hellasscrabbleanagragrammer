"""Greek word checker and anagram finder for the supplied Excel word list."""

from __future__ import annotations

import unicodedata
from collections import Counter
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import webbrowser

from PIL import Image, ImageTk


SOURCE_URL = "https://www.openbook.gr/oi-lexeis-2-8-grammaton-scrabble/"
INPUT_PLACEHOLDER = "π.χ. ΚΑΣΤΟΡΑΣ ή ΑΒΓ*"
APP_BG = "#EAF4FC"
CARD_BG = "#FFFFFF"
BLUE = "#2F6590"
BLUE_DARK = "#214B70"
YELLOW = "#FFF0B3"


def normalize(text: str) -> str:
    """Normalize Greek accents, case, and final sigma for dictionary matching."""
    text = unicodedata.normalize("NFD", text.strip().upper().replace("ς", "σ"))
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def is_greek_input(text: str, allow_wildcards: bool = False) -> bool:
    """Accept Greek letters (and, for anagrams, up to the caller to validate *)."""
    saw_letter = False
    for char in text:
        if allow_wildcards and char == "*":
            continue
        category = unicodedata.category(char)
        if category.startswith("M"):
            if not saw_letter:
                return False
            continue
        if category.startswith("L") and "GREEK" in unicodedata.name(char, ""):
            saw_letter = True
            continue
        return False
    return True


def load_words(path: Path) -> tuple[set[str], dict[str, str]]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError("Λείπει η βιβλιοθήκη openpyxl. Εγκαταστήστε την με: pip install -r requirements.txt") from exc

    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.worksheets[0]
    words: set[str] = set()
    meanings: dict[str, str] = {}
    try:
        for word_value, meaning_value in sheet.iter_rows(min_col=1, max_col=2, values_only=True):
            if isinstance(word_value, str):
                word = normalize(word_value)
                if word and word.isalpha():
                    words.add(word)
                    if isinstance(meaning_value, str) and meaning_value.strip():
                        meanings[word] = meaning_value.strip()
    finally:
        workbook.close()
    if not words:
        raise ValueError("Δεν βρέθηκαν λέξεις στην πρώτη στήλη του πρώτου φύλλου.")
    return words, meanings


class WordApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Αναγραμματισμός λέξεων - Ελληνικό Αγωνιστικό Σκραμπλ")
        self.geometry("1040x800")
        self.minsize(760, 620)
        self.configure(bg=APP_BG)
        self.words: set[str] = set()
        self.meanings: dict[str, str] = {}
        self.meaning_tooltip = None
        self.meaning_tooltip_label = None
        self.source = tk.StringVar(value="Δεν έχει φορτωθεί λίστα")
        self.status = tk.StringVar(value="")
        self._build_ui()
        self.after(100, self.load_default)

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("App.TFrame", background=APP_BG)
        style.configure("Card.TFrame", background=CARD_BG)
        style.configure("Card.TLabelframe", background=CARD_BG, bordercolor="#C9DCEC")
        style.configure("Card.TLabelframe.Label", background=CARD_BG, foreground=BLUE_DARK, font=("Segoe UI", 10, "bold"))
        style.configure("App.TLabel", background=APP_BG, foreground=BLUE_DARK)
        style.configure("Card.TLabel", background=CARD_BG, foreground=BLUE_DARK)
        style.configure("Title.TLabel", background=APP_BG, foreground=BLUE_DARK, font=("Segoe UI", 19, "bold"))
        style.configure("App.TButton", background=YELLOW, foreground=BLUE_DARK, padding=(12, 7), font=("Segoe UI", 10, "bold"))
        style.map("App.TButton", background=[("active", "#FFE58A")])

        outer = ttk.Frame(self, padding=18, style="App.TFrame")
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer, style="App.TFrame")
        header.pack(fill="x", pady=(0, 8))
        logo_path = Path(__file__).parent / "ΕΛΑ ΣΚΡΑΜΠΛ LOGO.png"
        if logo_path.exists():
            logo_image = Image.open(logo_path).convert("RGBA")
            logo_image.thumbnail((112, 100), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            ttk.Label(header, image=self.logo_photo, style="App.TLabel").pack(side="left", padx=(0, 14))
        source_card = ttk.Frame(header, padding=8, style="Card.TFrame")
        source_card.pack(side="right", anchor="n")
        cover_path = Path(__file__).parent / "oi-lekseis-2-8-grammaton-scrabble.jpg"
        if cover_path.exists():
            cover = Image.open(cover_path).convert("RGB")
            cover.thumbnail((62, 92), Image.Resampling.LANCZOS)
            self.cover_photo = ImageTk.PhotoImage(cover)
            cover_label = tk.Label(source_card, image=self.cover_photo, cursor="hand2", bg=CARD_BG, borderwidth=0)
            cover_label.pack(side="right", padx=(10, 0))
            cover_label.bind("<Button-1>", self.open_dictionary_source)
        source_info = ttk.Frame(source_card, style="Card.TFrame")
        source_info.pack(side="left", fill="x", expand=True, anchor="center")
        ttk.Label(source_info, text="Πηγή λεξικού", font=("Segoe UI", 10, "bold"), style="Card.TLabel").pack(anchor="w")
        source_link = tk.Label(source_info, text="«Οι λέξεις 2-8 γραμμάτων» — Ελληνικό Αγωνιστικό Σκραμπλ",
                               fg="#1769AA", bg=CARD_BG, cursor="hand2", font=("Segoe UI", 10, "underline"), anchor="w")
        source_link.pack(anchor="w", pady=(2, 0))
        source_link.bind("<Button-1>", self.open_dictionary_source)

        ttk.Label(header, text="Αναγραμματισμός λέξεων -\nΕλληνικό Αγωνιστικό Σκραμπλ", style="Title.TLabel",
                  anchor="center", justify="center").pack(side="left", fill="x", expand=True, padx=10)

        source_line = ttk.Frame(outer, style="App.TFrame")
        source_line.pack(fill="x", pady=(0, 12))
        ttk.Label(source_line, textvariable=self.source, style="App.TLabel").pack(side="left", anchor="w")

        tools = ttk.LabelFrame(outer, text="", padding=12, style="Card.TLabelframe")
        tools.pack(fill="x", pady=(0, 12))
        ttk.Label(tools, text="Έλεγχος και αναγραμματισμός", font=("Segoe UI", 12, "bold"),
                  style="Card.TLabel", anchor="center").pack(fill="x")
        ttk.Label(tools, text="Γράψε μία λέξη για έλεγχο.\nΑναγραμματισμός από 2–8 γράμματα.\nΤο * χρησιμοποιείται ως μπαλαντέρ στον αναγραμματισμό (έως 2 *).",
                  wraplength=900, justify="center", anchor="center", style="Card.TLabel").pack(fill="x", pady=(9, 0))
        self.input_entry = ttk.Entry(tools, font=("Segoe UI", 17, "bold"), justify="center")
        self.input_entry.pack(fill="x", pady=9, ipady=4)
        self._placeholder_visible = False
        self.input_entry.bind("<FocusIn>", self.on_input_focus_in)
        self.input_entry.bind("<FocusOut>", self.on_input_focus_out)
        self.input_entry.bind("<Return>", lambda _event: self.check_word())
        self.input_entry.bind("<KeyRelease>", self.on_input_changed)
        self.input_entry.bind("<<Paste>>", self.on_input_changed)
        self.input_entry.bind("<<Cut>>", self.on_input_changed)
        self.show_input_placeholder()
        buttons = ttk.Frame(tools, style="Card.TFrame")
        buttons.pack(anchor="center")
        ttk.Button(buttons, text="Έλεγχος λέξης", command=self.check_word, style="App.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Αναγραμματισμός", command=self.find_anagrams, style="App.TButton").pack(side="left")
        ttk.Button(buttons, text="Ερμηνεία", command=self.show_meaning, style="App.TButton").pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Έλεγχος πολλών λέξεων", command=self.check_multiple_words, style="App.TButton").pack(side="left", padx=(8, 0))
        self.check_result = ttk.Label(tools, text="", font=("Segoe UI", 11, "bold"), style="Card.TLabel")
        self.check_result.pack(anchor="center", pady=(8, 0))
        extra_buttons = ttk.Frame(tools, style="Card.TFrame")
        extra_buttons.pack(anchor="center", pady=(8, 0))
        ttk.Button(extra_buttons, text="Αρχίζουν από", command=lambda: self.search_by_letters("starts"), style="App.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(extra_buttons, text="Τελειώνουν σε", command=lambda: self.search_by_letters("ends"), style="App.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(extra_buttons, text="Περιέχουν", command=lambda: self.search_by_letters("contains"), style="App.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(extra_buttons, text="Αναγραμματισμός με σταθερό γράμμα", command=self.find_fixed_letter_anagrams, style="App.TButton").pack(side="left")

        anagrams = ttk.LabelFrame(outer, text="Αποτελέσματα ανά μήκος λέξης", padding=10, style="Card.TLabelframe")
        anagrams.pack(fill="both", expand=True)
        results_frame = ttk.Frame(anagrams, style="Card.TFrame")
        results_frame.pack(fill="both", expand=True)
        self.results = tk.Text(results_frame, wrap="word", font=("Segoe UI", 11), bg="#F7FBFF", fg=BLUE_DARK,
                               relief="flat", padx=10, pady=8, state="disabled", spacing1=4, spacing3=5)
        y_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results.yview)
        self.results.configure(yscrollcommand=y_scrollbar.set)
        self.results.pack(side="left", fill="both", expand=True)
        y_scrollbar.pack(side="right", fill="y")
        self.results.tag_configure("length", foreground=BLUE, font=("Segoe UI", 11, "bold"), tabs=(130,))
        self.results.tag_configure("words", foreground=BLUE_DARK)
        self.results.tag_configure("meaning", underline=True)
        self.results.bind("<Motion>", self.on_results_motion)
        self.results.bind("<Leave>", self.hide_meaning_tooltip)

        footer = ttk.Frame(outer, style="App.TFrame")
        footer.pack(fill="x", pady=(12, 0))
        ttk.Label(footer, textvariable=self.status, style="App.TLabel").pack(side="left", anchor="w")
        ttk.Button(footer, text="Επιλογή αρχείου Excel…", command=self.choose_file, style="App.TButton").pack(side="right")


    def load_default(self) -> None:
        candidates = sorted(Path(__file__).parent.glob("*.xlsx"))
        if candidates:
            self.load_file(candidates[0])
        else:
            self.status.set("Τοποθέτησε το Excel στον φάκελο της εφαρμογής ή επίλεξέ το παρακάτω.")

    def load_file(self, path: Path) -> None:
        try:
            self.words, self.meanings = load_words(path)
        except Exception as exc:
            messagebox.showerror("Σφάλμα φόρτωσης", str(exc))
            return
        self.source.set(f"Λίστα: {path.name} · {len(self.words):,} λέξεις")
        self.status.set("Η λίστα φορτώθηκε.")

    def open_dictionary_source(self, _event=None) -> None:
        webbrowser.open(SOURCE_URL)

    def clear_anagram_results(self) -> None:
        self.hide_meaning_tooltip()
        self.results.configure(state="normal")
        self.results.delete("1.0", tk.END)
        self.results.configure(state="disabled")
        self.status.set("")

    def clear_output(self) -> None:
        self.check_result.configure(text="")
        self.clear_anagram_results()

    def on_input_changed(self, event=None) -> None:
        if event is not None and getattr(event, "keysym", "") in {"Return", "KP_Enter"}:
            return
        self.check_result.configure(text="")
        self.status.set("")

    def show_input_placeholder(self) -> None:
        if not self.input_entry.get():
            self.input_entry.insert(0, INPUT_PLACEHOLDER)
            self.input_entry.configure(foreground="#91A9BC")
            self._placeholder_visible = True

    def on_input_focus_in(self, _event=None) -> None:
        if self._placeholder_visible:
            self.input_entry.delete(0, tk.END)
            self.input_entry.configure(foreground=BLUE_DARK)
            self._placeholder_visible = False

    def on_input_focus_out(self, _event=None) -> None:
        if not self.input_entry.get().strip():
            self.show_input_placeholder()

    def get_input_value(self) -> str:
        return "" if self._placeholder_visible else self.input_entry.get()

    def choose_file(self) -> None:
        selected = filedialog.askopenfilename(filetypes=[("Αρχεία Excel", "*.xlsx *.xlsm"), ("Όλα τα αρχεία", "*.*")])
        if selected:
            self.load_file(Path(selected))

    def check_word(self) -> None:
        self.clear_anagram_results()
        raw = self.get_input_value().strip()
        word = normalize(raw)
        if not raw:
            self.check_result.configure(text="Γράψε πρώτα μια λέξη.", foreground="#9a6700")
        elif len(raw.split()) > 1:
            self.check_result.configure(text="Γράψτε μόνο μία λέξη με ελληνικούς χαρακτήρες", foreground="#c62828")
        elif not is_greek_input(raw):
            self.check_result.configure(text="Γράψε μόνο με ελληνικούς χαρακτήρες.", foreground="#c62828")
        elif not self.words:
            self.check_result.configure(text="Δεν έχει φορτωθεί λίστα.", foreground="#9a6700")
        elif word in self.words:
            self.check_result.configure(text="✓ Υπάρχει στη λίστα λέξεων", foreground="#16803c")
        else:
            self.check_result.configure(text="✗ Δεν υπάρχει στη λίστα λέξεων", foreground="#c62828")

    def show_meaning(self) -> None:
        self.clear_anagram_results()
        raw = self.get_input_value().strip()
        word = normalize(raw)
        if not raw:
            self.check_result.configure(text="Γράψε πρώτα μια λέξη.", foreground="#9a6700")
        elif len(raw.split()) > 1:
            self.check_result.configure(text="Γράψτε μόνο μία λέξη με ελληνικούς χαρακτήρες", foreground="#c62828")
        elif not is_greek_input(raw):
            self.check_result.configure(text="Γράψε μόνο με ελληνικούς χαρακτήρες.", foreground="#c62828")
        elif not self.words:
            self.check_result.configure(text="Δεν έχει φορτωθεί λίστα.", foreground="#9a6700")
        elif word not in self.words:
            self.check_result.configure(text="Δεν υπάρχει η λέξη στη λίστα", foreground="#c62828")
        elif word in self.meanings:
            self.check_result.configure(text=f"{word}: {self.meanings[word]}", foreground=BLUE_DARK, wraplength=860)
        else:
            self.check_result.configure(
                text="Η λέξη βρέθηκε, Δεν υπάρχει ακόμα ερμήνευμα της λέξης",
                foreground="#9a6700", wraplength=860,
            )

    def check_multiple_words(self) -> None:
        self.clear_anagram_results()
        raw = self.get_input_value().strip()
        if not raw:
            self.check_result.configure(text="Γράψε τις λέξεις χωρισμένες με κενά.", foreground="#9a6700")
            return
        words = raw.split()
        if not 2 <= len(words) <= 8:
            self.check_result.configure(text="Γράψε από 2 έως 8 λέξεις, χωρισμένες με κενά.", foreground="#9a6700")
            return
        if any(not is_greek_input(word) for word in words):
            self.check_result.configure(text="Γράψε τις λέξεις μόνο με ελληνικούς χαρακτήρες.", foreground="#c62828")
            return
        if not self.words:
            self.check_result.configure(text="Δεν έχει φορτωθεί λίστα.", foreground="#9a6700")
            return

        found_all = all(normalize(word) in self.words for word in words)
        if not found_all:
            self.check_result.configure(text="Τουλάχιστον μία λέξη δε βρίσκεται στη λίστα", foreground="#c62828", wraplength=860)
        elif len(words) == 2:
            self.check_result.configure(text="Και Οι δύο λέξεις βρίσκονται στη λίστα", foreground="#16803c", wraplength=860)
        else:
            self.check_result.configure(text="Όλες οι επιλεγμένες λέξεις βρίσκονται στη λίστα", foreground="#16803c", wraplength=860)

    def search_by_letters(self, mode: str) -> None:
        self.clear_output()
        raw = self.get_input_value().strip()
        letters = normalize(raw)
        if not raw:
            self.status.set("Γράψε τουλάχιστον 3 ελληνικά γράμματα.")
            return
        if not is_greek_input(raw):
            self.status.set("Χρησιμοποίησε μόνο ελληνικούς χαρακτήρες.")
            return
        if len(letters) < 3:
            self.status.set("Χρειάζονται τουλάχιστον 3 γράμματα.")
            return
        if not self.words:
            self.status.set("Δεν έχει φορτωθεί λίστα.")
            return

        matches_by_length: dict[int, list[str]] = {}
        for word in self.words:
            matches = (word.startswith(letters) if mode == "starts" else
                       word.endswith(letters) if mode == "ends" else
                       letters in word)
            if matches:
                matches_by_length.setdefault(len(word), []).append(word)
        self.display_grouped_results(matches_by_length, "Δεν βρέθηκαν λέξεις με αυτά τα γράμματα.")

    def find_fixed_letter_anagrams(self) -> None:
        self.clear_output()
        raw = self.get_input_value().strip()
        query = normalize(raw)
        query_letters = list(query)
        if not raw:
            self.status.set("Γράψε από 2 έως 8 ελληνικά γράμματα.")
            return
        if not is_greek_input(raw):
            self.status.set("Χρησιμοποίησε μόνο ελληνικούς χαρακτήρες.")
            return
        if not 2 <= len(query_letters) <= 8:
            self.status.set("Δώσε από 2 έως 8 ελληνικά γράμματα.")
            return
        if not self.words:
            self.status.set("Δεν έχει φορτωθεί λίστα.")
            return

        fixed_raw = simpledialog.askstring("Σταθερό γράμμα", "Ποιο γράμμα θέλεις να είναι σταθερό;", parent=self)
        if fixed_raw is None:
            return
        fixed_letter = normalize(fixed_raw.strip())
        if not is_greek_input(fixed_raw) or len(fixed_letter) != 1:
            self.status.set("Δώσε ένα μόνο ελληνικό γράμμα.")
            return
        if fixed_letter not in query_letters:
            self.status.set("Το σταθερό γράμμα πρέπει να υπάρχει στα διαθέσιμα γράμματα.")
            return

        position = simpledialog.askinteger(
            "Θέση σταθερού γράμματος",
            f"Σε ποια θέση θέλεις το {fixed_letter}; (1–{len(query_letters)})",
            parent=self, minvalue=1, maxvalue=len(query_letters),
        )
        if position is None:
            return

        available = Counter(query_letters)
        available[fixed_letter] -= 1
        matches_by_length: dict[int, list[str]] = {}
        for word in self.words:
            if len(word) < 2 or len(word) > len(query_letters) or position > len(word):
                continue
            if word[position - 1] != fixed_letter:
                continue
            needed = Counter(word)
            needed[fixed_letter] -= 1
            if all(count <= available[letter] for letter, count in needed.items()):
                matches_by_length.setdefault(len(word), []).append(word)
        self.display_grouped_results(
            matches_by_length,
            "Δεν βρέθηκαν λέξεις με αυτό το σταθερό γράμμα και τη θέση.",
        )

    def display_grouped_results(self, matches_by_length: dict[int, list[str]], empty_message: str) -> None:
        self.hide_meaning_tooltip()
        self.results.configure(state="normal")
        self.results.delete("1.0", tk.END)
        lengths = sorted(matches_by_length, reverse=True)
        for length in lengths:
            words = sorted(matches_by_length[length])
            self.results.insert(tk.END, f"{length} γράμματα\t", "length")
            for index, word in enumerate(words):
                if index:
                    self.results.insert(tk.END, " · ", "words")
                start = self.results.index(tk.END)
                self.results.insert(tk.END, word, "words")
                if self.meanings.get(normalize(word)):
                    self.results.tag_add("meaning", start, self.results.index(tk.END))
            self.results.insert(tk.END, "\n", "words")
        if not lengths:
            self.results.insert(tk.END, empty_message, "words")
        self.results.configure(state="disabled")
        total = sum(len(words) for words in matches_by_length.values())
        if total:
            self.status.set(f"Βρέθηκαν {total:,} λέξεις σε {len(lengths)} μήκη.")
        else:
            self.status.set(empty_message)

    def on_results_motion(self, event) -> None:
        index = self.results.index(f"@{event.x},{event.y}")
        column = int(index.split(".")[1])
        line = self.results.get(f"{index} linestart", f"{index} lineend")
        tab = line.find("\t")
        if tab < 0:
            self.hide_meaning_tooltip()
            return

        content = line[tab + 1:]
        offset = column - tab - 1
        if offset < 0:
            self.hide_meaning_tooltip()
            return
        delimiter = " · "
        cursor = 0
        for word in content.split(delimiter):
            end = cursor + len(word)
            if cursor <= offset < end:
                meaning = self.meanings.get(normalize(word))
                if meaning:
                    self.show_meaning_tooltip(meaning, event.x_root + 14, event.y_root + 14)
                    return
                break
            cursor = end + len(delimiter)
        self.hide_meaning_tooltip()

    def show_meaning_tooltip(self, meaning: str, x: int, y: int) -> None:
        self.results.configure(cursor="hand2")
        if self.meaning_tooltip is None:
            self.meaning_tooltip = tk.Toplevel(self)
            self.meaning_tooltip.wm_overrideredirect(True)
            self.meaning_tooltip_label = tk.Label(
                self.meaning_tooltip, background="#FFF6CC", foreground=BLUE_DARK,
                relief="solid", borderwidth=1, font=("Segoe UI", 10),
                justify="left", wraplength=420, padx=8, pady=5,
            )
            self.meaning_tooltip_label.pack()
        self.meaning_tooltip_label.configure(text=meaning)
        self.meaning_tooltip.geometry(f"+{x}+{y}")

    def hide_meaning_tooltip(self, _event=None) -> None:
        if self.meaning_tooltip is not None:
            self.meaning_tooltip.destroy()
            self.meaning_tooltip = None
            self.meaning_tooltip_label = None
        if hasattr(self, "results"):
            self.results.configure(cursor="xterm")

    def find_anagrams(self) -> None:
        raw = self.get_input_value().strip()
        query = normalize(raw)
        stars = query.count("*")
        letters = query.replace("*", "")
        self.results.configure(state="normal")
        self.results.delete("1.0", tk.END)
        self.results.configure(state="disabled")
        if not query:
            self.status.set("Γράψε τα διαθέσιμα γράμματα.")
            return
        if not is_greek_input(raw, allow_wildcards=True):
            self.status.set("Γράψε μόνο ελληνικά γράμματα και το σύμβολο *.")
            return
        if stars > 2:
            self.status.set("Επιτρέπονται έως 2 μπαλαντέρ (*).")
            return
        if len(query) > 8:
            self.status.set("Το λεξικό περιλαμβάνει λέξεις έως 8 γράμματα. Δώσε έως 8 γράμματα συνολικά.")
            return
        if any(not ch.isalpha() for ch in letters):
            self.status.set("Χρησιμοποίησε γράμματα και το σύμβολο *.")
            return
        if not self.words:
            self.status.set("Δεν έχει φορτωθεί λίστα.")
            return

        available = Counter(letters)
        matches_by_length: dict[int, list[str]] = {}
        for word in self.words:
            if not 2 <= len(word) <= len(query):
                continue
            needed = Counter(word)
            missing = sum(max(0, count - available[letter]) for letter, count in needed.items())
            if missing <= stars:
                matches_by_length.setdefault(len(word), []).append(word)
        for matches in matches_by_length.values():
            matches.sort()

        self.display_grouped_results(matches_by_length, "Δεν βρέθηκαν λέξεις με αυτά τα γράμματα.")


if __name__ == "__main__":
    WordApp().mainloop()
