"use strict";

const DICTIONARY_URL = "./data/words.tsv?v=20261125-2";
const alphabet = Array.from("ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ");
const letterCount = document.querySelector("#letter-count");
const wildcardCount = document.querySelector("#wildcard-count");
const newRackButton = document.querySelector("#new-rack-button");
const shuffleButton = document.querySelector("#shuffle-button");
const rackElement = document.querySelector("#letter-rack");
const status = document.querySelector("#practice-status");
const answerForm = document.querySelector("#answer-form");
const answerInput = document.querySelector("#practice-answer");
const answerResult = document.querySelector("#answer-result");

let dictionary = new Set();
let wordsByLength = new Map();
let currentRack = [];
let currentWildcardCount = 0;

function normalize(value) {
  return value.trim().toLocaleUpperCase("el-GR").replace(/ς/g, "Σ")
    .normalize("NFD").replace(/\p{M}/gu, "");
}

function randomIndex(max) {
  if (max <= 1) return 0;
  const values = new Uint32Array(1);
  crypto.getRandomValues(values);
  return values[0] % max;
}

function shuffle(values) {
  const shuffled = [...values];
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const other = randomIndex(index + 1);
    [shuffled[index], shuffled[other]] = [shuffled[other], shuffled[index]];
  }
  return shuffled;
}

function renderRack() {
  rackElement.replaceChildren();
  currentRack.forEach((letter) => {
    const tile = document.createElement("span");
    tile.className = `rack-tile${letter === "*" ? " is-wildcard" : ""}`;
    tile.textContent = letter;
    rackElement.append(tile);
  });
  rackElement.setAttribute("aria-label", `Γράμματα: ${currentRack.join(" ")}`);
}

function makeRack() {
  const count = Number(letterCount.value);
  const wildcards = Number(wildcardCount.value);
  const candidates = wordsByLength.get(count) ?? [];
  if (!candidates.length) {
    status.textContent = `Δεν υπάρχουν λέξεις ${count} γραμμάτων στο λεξικό.`;
    return;
  }

  // Use an actual dictionary word as the rack source so every draw has at least one solution.
  const solution = [...candidates[randomIndex(candidates.length)]];
  const wildcardPositions = new Set();
  while (wildcardPositions.size < wildcards) wildcardPositions.add(randomIndex(solution.length));
  currentRack = shuffle(solution.map((letter, index) => wildcardPositions.has(index) ? "*" : letter));
  currentWildcardCount = wildcards;
  renderRack();
  answerForm.hidden = false;
  answerInput.value = "";
  answerResult.textContent = "";
  answerResult.className = "word-result";
  status.textContent = "Βρες μία λέξη που χρησιμοποιεί όλα τα γράμματα. Το * αντικαθιστά ένα γράμμα.";
  shuffleButton.disabled = false;
  answerInput.focus();
}

function checkAnswer(event) {
  event.preventDefault();
  const answer = normalize(answerInput.value);
  if (!answer) {
    answerResult.textContent = "Γράψε πρώτα τη λέξη που βρήκες.";
    answerResult.className = "word-result info";
    return;
  }
  if ([...answer].some((letter) => !alphabet.includes(letter))) {
    answerResult.textContent = "Γράψε μόνο ελληνικούς χαρακτήρες.";
    answerResult.className = "word-result error";
    return;
  }
  if (!dictionary.has(answer)) {
    answerResult.textContent = `Η λέξη «${answer}» δεν βρέθηκε στη λίστα.`;
    answerResult.className = "word-result error";
    return;
  }
  if ([...answer].length !== currentRack.length) {
    answerResult.textContent = "Η λέξη πρέπει να χρησιμοποιεί όλα τα γράμματα.";
    answerResult.className = "word-result error";
    return;
  }

  const available = new Map();
  for (const tile of currentRack) {
    if (tile !== "*") available.set(tile, (available.get(tile) ?? 0) + 1);
  }
  let missing = 0;
  for (const letter of answer) {
    const remaining = available.get(letter) ?? 0;
    if (remaining > 0) available.set(letter, remaining - 1);
    else missing += 1;
  }
  if (missing !== currentWildcardCount) {
    answerResult.textContent = "Η λέξη είναι αποδεκτή, αλλά δεν σχηματίζεται από αυτά τα γράμματα.";
    answerResult.className = "word-result error";
    return;
  }
  answerResult.textContent = `✓ Σωστά! Η λέξη «${answer}» βρίσκεται στη λίστα και σχηματίζεται από τα γράμματα.`;
  answerResult.className = "word-result success";
}

async function loadDictionary() {
  try {
    const response = await fetch(DICTIONARY_URL);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const text = await response.text();
    for (const line of text.split(/\r?\n/)) {
      if (!line) continue;
      const separator = line.indexOf("\t");
      const word = normalize(separator === -1 ? line : line.slice(0, separator));
      dictionary.add(word);
      const length = [...word].length;
      if (length === 7 || length === 8) {
        if (!wordsByLength.has(length)) wordsByLength.set(length, []);
        wordsByLength.get(length).push(word);
      }
    }
    status.textContent = `Το λεξικό φορτώθηκε · ${dictionary.size.toLocaleString("el-GR")} λέξεις.`;
    newRackButton.disabled = false;
    makeRack();
  } catch (error) {
    status.textContent = "Δεν ήταν δυνατή η φόρτωση του λεξικού. Έλεγξε τη σύνδεση και ανανέωσε τη σελίδα.";
    console.error("Dictionary load failed", error);
  }
}

newRackButton.addEventListener("click", makeRack);
shuffleButton.addEventListener("click", () => {
  currentRack = shuffle(currentRack);
  renderRack();
});
letterCount.addEventListener("change", makeRack);
wildcardCount.addEventListener("change", makeRack);
answerForm.addEventListener("submit", checkAnswer);
loadDictionary();
