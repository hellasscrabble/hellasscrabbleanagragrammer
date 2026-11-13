"use strict";

const DICTIONARY_URL = "./data/words.tsv?v=20261114-1";
const SOURCE_URL = "https://www.openbook.gr/oi-lexeis-2-8-grammaton-scrabble/";
const ALPHABET = Array.from("ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ");
const GREEK_INDEX = new Map(ALPHABET.map((letter, index) => [letter, index]));
const LATIN_TO_GREEK_KEY = new Map(Object.entries({
  a: "α", b: "β", c: "ψ", d: "δ", e: "ε", f: "φ", g: "γ", h: "η", i: "ι",
  j: "ξ", k: "κ", l: "λ", m: "μ", n: "ν", o: "ο", p: "π", q: ";", r: "ρ",
  s: "σ", t: "τ", u: "θ", v: "ω", w: "ς", x: "χ", y: "υ", z: "ζ",
  A: "Α", B: "Β", C: "Ψ", D: "Δ", E: "Ε", F: "Φ", G: "Γ", H: "Η", I: "Ι",
  J: "Ξ", K: "Κ", L: "Λ", M: "Μ", N: "Ν", O: "Ο", P: "Π", Q: ";", R: "Ρ",
  S: "Σ", T: "Τ", U: "Θ", V: "Ω", W: "Σ", X: "Χ", Y: "Υ", Z: "Ζ",
}));

const input = document.querySelector("#word-input");
const checkButton = document.querySelector("#check-button");
const anagramButton = document.querySelector("#anagram-button");
const meaningButton = document.querySelector("#meaning-button");
const multipleCheckButton = document.querySelector("#multiple-check-button");
const startsWithButton = document.querySelector("#starts-with-button");
const endsWithButton = document.querySelector("#ends-with-button");
const containsButton = document.querySelector("#contains-button");
const fixedLetterButton = document.querySelector("#fixed-letter-button");
const wordResult = document.querySelector("#word-result");
const status = document.querySelector("#input-status");
const resultsPanel = document.querySelector("#anagram-panel");
const resultsTitle = document.querySelector("#results-title");
const results = document.querySelector("#results");
const resultCount = document.querySelector("#result-count");

let dictionary = new Map();
let ready = false;
let inputConversionTimer = null;

function normalize(value) {
  return value.trim().toLocaleUpperCase("el-GR").replace(/ς/g, "Σ")
    .normalize("NFD").replace(/\p{M}/gu, "");
}

function isGreekInput(value, allowStars = false) {
  let sawGreek = false;
  for (const char of value.trim()) {
    if (allowStars && char === "*") continue;
    if (/\p{M}/u.test(char)) {
      if (!sawGreek) return false;
      continue;
    }
    if (/\p{Script=Greek}/u.test(char) && /\p{L}/u.test(char)) {
      sawGreek = true;
      continue;
    }
    return false;
  }
  return true;
}

function convertLatinKeyboard(value) {
  return [...value].map((char) => LATIN_TO_GREEK_KEY.get(char) ?? char).join("");
}

function convertInputToGreek() {
  const original = input.value;
  const cursorStart = input.selectionStart ?? original.length;
  const cursorEnd = input.selectionEnd ?? cursorStart;
  const converted = convertLatinKeyboard(original).toLocaleUpperCase("el-GR");
  if (converted === original) return;

  input.value = converted;
  input.setSelectionRange(
    convertLatinKeyboard(original.slice(0, cursorStart)).toLocaleUpperCase("el-GR").length,
    convertLatinKeyboard(original.slice(0, cursorEnd)).toLocaleUpperCase("el-GR").length,
  );
}

function scheduleInputConversion() {
  if (inputConversionTimer !== null) window.clearTimeout(inputConversionTimer);
  inputConversionTimer = window.setTimeout(() => {
    inputConversionTimer = null;
    convertInputToGreek();
  }, 250);
}

function finalizeInputConversion() {
  if (inputConversionTimer !== null) window.clearTimeout(inputConversionTimer);
  inputConversionTimer = null;
  convertInputToGreek();
}

function showWordResult(message, kind = "info") {
  wordResult.textContent = message;
  wordResult.className = `word-result ${kind}`;
  results.replaceChildren();
  resultCount.textContent = "";
  resultsPanel.hidden = true;
}

function clearWordResult() {
  wordResult.textContent = "";
  wordResult.className = "word-result";
  status.textContent = "";
}

function clearOutput() {
  wordResult.textContent = "";
  wordResult.className = "word-result";
  status.textContent = "";
  results.replaceChildren();
  resultCount.textContent = "";
  resultsPanel.hidden = true;
}

function renderGroupedResults(groups, title, emptyMessage) {
  results.replaceChildren();
  resultsTitle.textContent = title;
  const lengths = [...groups.keys()].sort((a, b) => b - a);
  const total = lengths.reduce((sum, length) => sum + groups.get(length).length, 0);
  resultsPanel.hidden = false;
  if (total === 0) {
    results.append(Object.assign(document.createElement("p"), {
      className: "empty-results",
      textContent: emptyMessage,
    }));
    resultCount.textContent = "0 λέξεις";
    return;
  }

  for (const length of lengths) {
    const words = groups.get(length).sort((a, b) => a.localeCompare(b, "el"));
    const row = document.createElement("div");
    row.className = "length-row";
    const heading = document.createElement("span");
    heading.className = "length-label";
    heading.textContent = `${length} γράμματα (${groups.get(length).length.toLocaleString("el-GR")})`;
    const list = document.createElement("span");
    list.className = "word-list";
    words.forEach((word, index) => {
      if (index > 0) list.append(document.createTextNode(" · "));
      const meaning = dictionary.get(word);
      if (meaning) {
        const entry = document.createElement("span");
        entry.className = "word-entry";
        const wordElement = document.createElement("span");
        wordElement.textContent = word;
        wordElement.className = "word-with-meaning";
        if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
          wordElement.title = meaning;
        }
        wordElement.tabIndex = 0;
        wordElement.setAttribute("role", "button");
        wordElement.setAttribute("aria-label", `${word}, πάτησε για να δεις την ερμηνεία`);
        wordElement.setAttribute("aria-expanded", "false");

        const meaningPopup = document.createElement("span");
        meaningPopup.className = "word-meaning-popup";
        meaningPopup.textContent = meaning;
        meaningPopup.hidden = true;

        const closeOtherMeanings = () => {
          results.querySelectorAll(".word-meaning-popup").forEach((popup) => {
            popup.hidden = true;
            popup.previousElementSibling?.setAttribute("aria-expanded", "false");
          });
        };
        const toggleMeaning = () => {
          const shouldOpen = meaningPopup.hidden;
          closeOtherMeanings();
          meaningPopup.hidden = !shouldOpen;
          wordElement.setAttribute("aria-expanded", String(shouldOpen));
        };
        let suppressSyntheticClick = false;
        wordElement.addEventListener("pointerup", (event) => {
          if (event.pointerType !== "touch") return;
          toggleMeaning();
          suppressSyntheticClick = true;
          window.setTimeout(() => { suppressSyntheticClick = false; }, 500);
        });
        wordElement.addEventListener("click", () => {
          if (suppressSyntheticClick) {
            suppressSyntheticClick = false;
            return;
          }
          toggleMeaning();
        });
        wordElement.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            toggleMeaning();
          }
        });

        entry.append(wordElement, meaningPopup);
        list.append(entry);
      } else {
        list.append(document.createTextNode(word));
      }
    });
    row.append(heading, list);
    results.append(row);
  }
  resultCount.textContent = `${total.toLocaleString("el-GR")} λέξεις`;
}

function checkWord() {
  finalizeInputConversion();
  const raw = input.value.trim();
  if (!raw) return showWordResult("Γράψε πρώτα μια λέξη.");
  if (raw.split(/\s+/).length > 1) {
    return showWordResult("Γράψτε μόνο μία λέξη με ελληνικούς χαρακτήρες", "error");
  }
  if (!isGreekInput(raw)) return showWordResult("Γράψε μόνο με ελληνικούς χαρακτήρες.", "error");
  if (!ready) return showWordResult("Το λεξικό φορτώνεται ακόμη. Περίμενε λίγο.");

  const word = normalize(raw);
  if ([...word].length > 10) {
    return showWordResult("Γράψτε λέξεις έως 10 γράμματα.", "error");
  }
  if (dictionary.has(word)) {
    showWordResult(`✓ Η λέξη «${word}» βρέθηκε στη λίστα.`, "success");
  } else if ([...word].length >= 9) {
    showWordResult(`✗ Η λέξη «${word}» δεν βρέθηκε στη λίστα. Συμβουλευτείτε τα λεξικά βάσης.`, "error");
  } else {
    showWordResult(`✗ Η λέξη «${word}» δεν βρέθηκε στη λίστα.`, "error");
  }
}

function showMeaning() {
  finalizeInputConversion();
  const raw = input.value.trim();
  if (!raw) return showWordResult("Γράψε πρώτα μια λέξη.");
  if (raw.split(/\s+/).length > 1) {
    return showWordResult("Γράψτε μόνο μία λέξη με ελληνικούς χαρακτήρες", "error");
  }
  if (!isGreekInput(raw)) return showWordResult("Γράψε μόνο με ελληνικούς χαρακτήρες.", "error");
  if (!ready) return showWordResult("Το λεξικό φορτώνεται ακόμη. Περίμενε λίγο.");

  const word = normalize(raw);
  if (!dictionary.has(word)) return showWordResult("Δεν υπάρχει η λέξη στη λίστα", "error");
  const meaning = dictionary.get(word);
  if (meaning) showWordResult(`${word}: ${meaning}`, "success");
  else showWordResult("Η λέξη βρέθηκε, Δεν υπάρχει ακόμα ερμήνευμα της λέξης", "info");
}

function checkMultipleWords() {
  finalizeInputConversion();
  const raw = input.value.trim();
  if (!raw) return showWordResult("Γράψε τις λέξεις χωρισμένες με κενά.");
  const words = raw.split(/\s+/);
  if (words.length < 2 || words.length > 8) {
    return showWordResult("Γράψε από 2 έως 8 λέξεις, χωρισμένες με κενά.");
  }
  if (words.some((word) => !isGreekInput(word))) {
    return showWordResult("Γράψε τις λέξεις μόνο με ελληνικούς χαρακτήρες.", "error");
  }
  if (!ready) return showWordResult("Το λεξικό φορτώνεται ακόμη. Περίμενε λίγο.");

  if (!words.every((word) => dictionary.has(normalize(word)))) {
    return showWordResult("Τουλάχιστον μία λέξη δε βρίσκεται στη λίστα", "error");
  }
  if (words.length === 2) {
    return showWordResult("Και οι δύο λέξεις βρίσκονται στη λίστα", "success");
  }
  return showWordResult("Όλες οι επιλεγμένες λέξεις βρίσκονται στη λίστα", "success");
}

function searchByLetters(mode) {
  finalizeInputConversion();
  clearOutput();
  const raw = input.value.trim();
  const letters = normalize(raw);
  if (!raw) {
    status.textContent = "Γράψε τουλάχιστον 3 ελληνικά γράμματα.";
    return;
  }
  if (!isGreekInput(raw)) {
    status.textContent = "Χρησιμοποίησε μόνο ελληνικούς χαρακτήρες.";
    return;
  }
  if ([...letters].length < 3) {
    status.textContent = "Χρειάζονται τουλάχιστον 3 γράμματα.";
    return;
  }
  if (!ready) {
    status.textContent = "Το λεξικό φορτώνεται ακόμη. Περίμενε λίγο.";
    return;
  }

  const match = mode === "starts"
    ? (word) => word.startsWith(letters)
    : mode === "ends"
      ? (word) => word.endsWith(letters)
      : (word) => word.includes(letters);
  const groups = new Map();
  for (const word of dictionary.keys()) {
    if (!match(word)) continue;
    const length = [...word].length;
    if (!groups.has(length)) groups.set(length, []);
    groups.get(length).push(word);
  }
  const title = mode === "starts" ? `Λέξεις που αρχίζουν από ${letters}`
    : mode === "ends" ? `Λέξεις που τελειώνουν σε ${letters}`
      : `Λέξεις που περιέχουν ${letters}`;
  renderGroupedResults(groups, title, "Δεν βρέθηκαν λέξεις με αυτά τα γράμματα.");
}

function findFixedLetterAnagrams() {
  finalizeInputConversion();
  clearOutput();
  const raw = input.value.trim();
  const query = normalize(raw);
  const queryLetters = [...query];
  if (!raw) {
    status.textContent = "Γράψε από 2 έως 8 ελληνικά γράμματα.";
    return;
  }
  if (!isGreekInput(raw, true)) {
    status.textContent = "Χρησιμοποίησε μόνο ελληνικούς χαρακτήρες και το σύμβολο *.";
    return;
  }
  if (queryLetters.length < 2 || queryLetters.length > 8) {
    status.textContent = "Δώσε από 2 έως 8 ελληνικά γράμματα.";
    return;
  }
  const wildcardCount = queryLetters.filter((char) => char === "*").length;
  if (wildcardCount > 2) {
    status.textContent = "Επιτρέπονται έως 2 μπαλαντέρ (*).";
    return;
  }
  if (!ready) {
    status.textContent = "Το λεξικό φορτώνεται ακόμη. Περίμενε λίγο.";
    return;
  }

  const fixedRaw = window.prompt("Ποιο γράμμα θέλεις να είναι σταθερό;");
  if (fixedRaw === null) return;
  const fixedLetter = normalize(fixedRaw.trim());
  if (!isGreekInput(fixedRaw) || [...fixedLetter].length !== 1) {
    status.textContent = "Δώσε ένα μόνο ελληνικό γράμμα.";
    return;
  }
  if (!queryLetters.includes(fixedLetter)) {
    status.textContent = "Το σταθερό γράμμα πρέπει να υπάρχει στα διαθέσιμα γράμματα.";
    return;
  }

  const positionRaw = window.prompt(`Σε ποια θέση θέλεις το ${fixedLetter}; (1–${queryLetters.length})`);
  if (positionRaw === null) return;
  if (!/^\d+$/.test(positionRaw.trim())) {
    status.textContent = "Δώσε τη θέση ως αριθμό.";
    return;
  }
  const position = Number(positionRaw);
  if (position < 1 || position > queryLetters.length) {
    status.textContent = `Η θέση πρέπει να είναι από 1 έως ${queryLetters.length}.`;
    return;
  }

  const available = new Int8Array(ALPHABET.length);
  for (const char of queryLetters) {
    if (char !== "*") available[GREEK_INDEX.get(char)] += 1;
  }
  available[GREEK_INDEX.get(fixedLetter)] -= 1;
  const groups = new Map();
  for (const word of dictionary.keys()) {
    const wordLetters = [...word];
    if (wordLetters.length < 2 || wordLetters.length > queryLetters.length
      || position > wordLetters.length || wordLetters[position - 1] !== fixedLetter) continue;
    const remaining = available.slice();
    let wildcardsLeft = wildcardCount;
    let fits = true;
    for (let i = 0; i < wordLetters.length; i += 1) {
      if (i === position - 1) continue;
      const index = GREEK_INDEX.get(wordLetters[i]);
      if (index === undefined) {
        fits = false;
        break;
      }
      if (remaining[index] > 0) remaining[index] -= 1;
      else if (wildcardsLeft > 0) wildcardsLeft -= 1;
      else {
        fits = false;
        break;
      }
    }
    if (fits) {
      if (!groups.has(wordLetters.length)) groups.set(wordLetters.length, []);
      groups.get(wordLetters.length).push(word);
    }
  }
  renderGroupedResults(groups, `Σταθερό ${fixedLetter} στη θέση ${position}`,
    "Δεν βρέθηκαν λέξεις με αυτό το σταθερό γράμμα και τη θέση.");
}

function findAnagrams() {
  finalizeInputConversion();
  clearOutput();
  const raw = input.value.trim();
  const query = normalize(raw);
  if (!query) {
    status.textContent = "Γράψε τα διαθέσιμα γράμματα.";
    return;
  }
  if (!isGreekInput(raw, true)) {
    status.textContent = "Γράψε μόνο ελληνικά γράμματα και το σύμβολο *.";
    return;
  }
  const stars = [...query].filter((char) => char === "*").length;
  if (stars > 2) {
    status.textContent = "Επιτρέπονται έως 2 μπαλαντέρ (*).";
    return;
  }
  if ([...query].length > 8) {
    status.textContent = "Το λεξικό περιλαμβάνει λέξεις έως 8 γράμματα. Δώσε έως 8 γράμματα συνολικά.";
    return;
  }
  if (!ready) {
    status.textContent = "Το λεξικό φορτώνεται ακόμη. Περίμενε λίγο.";
    return;
  }

  const available = new Int8Array(ALPHABET.length);
  const queryLength = [...query].length;
  for (const char of query) {
    const index = GREEK_INDEX.get(char);
    if (char !== "*" && index !== undefined) available[index] += 1;
  }

  const groups = new Map();
  for (const word of dictionary.keys()) {
    const length = [...word].length;
    if (length < 2 || length > queryLength) continue;
    const remaining = available.slice();
    let missing = 0;
    for (const char of word) {
      const index = GREEK_INDEX.get(char);
      if (index === undefined) {
        missing = stars + 1;
        break;
      }
      if (remaining[index] > 0) remaining[index] -= 1;
      else missing += 1;
      if (missing > stars) break;
    }
    if (missing <= stars) {
      if (!groups.has(length)) groups.set(length, []);
      groups.get(length).push(word);
    }
  }

  renderGroupedResults(groups, "Αποτελέσματα αναγραμματισμού", "Δεν βρέθηκαν λέξεις με αυτά τα γράμματα.");
}

async function loadDictionary() {
  try {
    const embedded = document.querySelector("#embedded-dictionary");
    if (embedded) {
      dictionary = new Map(JSON.parse(embedded.textContent));
      ready = true;
      status.textContent = `Το λεξικό φορτώθηκε · ${dictionary.size.toLocaleString("el-GR")} λέξεις.`;
      return;
    }
    const response = await fetch(DICTIONARY_URL);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const text = await response.text();
    for (const line of text.split(/\r?\n/)) {
      if (!line) continue;
      const separator = line.indexOf("\t");
      const word = separator === -1 ? line : line.slice(0, separator);
      const meaning = separator === -1 ? "" : line.slice(separator + 1);
      dictionary.set(normalize(word), meaning);
    }
    ready = true;
    status.textContent = `Το λεξικό φορτώθηκε · ${dictionary.size.toLocaleString("el-GR")} λέξεις.`;
  } catch (error) {
    status.textContent = "Δεν ήταν δυνατή η φόρτωση του λεξικού. Έλεγξε τη σύνδεση και ανανέωσε τη σελίδα.";
    console.error("Dictionary load failed", error);
  }
}

checkButton.addEventListener("click", checkWord);
anagramButton.addEventListener("click", findAnagrams);
meaningButton.addEventListener("click", showMeaning);
multipleCheckButton.addEventListener("click", checkMultipleWords);
startsWithButton.addEventListener("click", () => searchByLetters("starts"));
endsWithButton.addEventListener("click", () => searchByLetters("ends"));
containsButton.addEventListener("click", () => searchByLetters("contains"));
fixedLetterButton.addEventListener("click", findFixedLetterAnagrams);
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter") checkWord();
});
input.addEventListener("input", (event) => {
  clearWordResult();
  if (!event.isComposing) scheduleInputConversion();
});
input.addEventListener("compositionend", () => {
  scheduleInputConversion();
});
// Let visitors select the displayed words and meanings, while blocking clipboard actions.
document.addEventListener("copy", (event) => event.preventDefault());
document.addEventListener("cut", (event) => event.preventDefault());
document.addEventListener("paste", (event) => event.preventDefault());
document.addEventListener("click", (event) => {
  if (event.target.closest?.(".word-entry")) return;
  results.querySelectorAll(".word-meaning-popup").forEach((popup) => {
    popup.hidden = true;
    popup.previousElementSibling?.setAttribute("aria-expanded", "false");
  });
});
loadDictionary();

if ("serviceWorker" in navigator && location.protocol.startsWith("http")) {
  window.addEventListener("load", () => navigator.serviceWorker.register("./service-worker.js").catch(console.warn));
}
