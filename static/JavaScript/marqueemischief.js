window.addEventListener("load", myInit, true);

const originalMessageLayouts = new WeakMap();

function originalMessage() {
    return document.getElementById("tryItBox").dataset.originalMessage;
}

function setTryItOriginalMessage(message) {
    const box = document.getElementById("tryItBox");
    const marquee = document.querySelector(".marquee-stage .marquee-message");
    const normalizedMessage = message.toUpperCase().split(/\s+/).filter(Boolean).join(" ");
    const wrap = (text, width) => {
        const lines = [];
        let line = "";
        for (let word of text.split(" ").filter(Boolean)) {
            while (word.length > width) {
                if (line) {
                    lines.push(line);
                    line = "";
                }
                lines.push(word.slice(0, width));
                word = word.slice(width);
            }
            if (!line) {
                line = word;
            } else if (line.length + 1 + word.length <= width) {
                line += " " + word;
            } else {
                lines.push(line);
                line = word;
            }
        }
        if (line) {
            lines.push(line);
        }
        return lines;
    };

    let width = 25;
    let lines = wrap(normalizedMessage, width);
    while (lines.length > 4) {
        lines = wrap(normalizedMessage, ++width);
    }
    if (!lines.length) {
        lines = [""];
    }

    const fontSize = Math.max(14, Math.round(28 * 25 / width));
    const rowLineHeight = `${fontSize * 1.1 + 3}px`;
    [marquee, box.closest(".marquee-message")].forEach((frame) => {
        frame.style.boxSizing = "border-box";
        frame.style.width = "fit-content";
        frame.style.height = "";
        frame.style.maxWidth = `min(100%, ${width}ch)`;
        frame.style.fontSize = `${fontSize}px`;
    });
    box.style.lineHeight = rowLineHeight;
    box.style.minHeight = "";

    marquee.replaceChildren(...lines.map((text) => {
        const row = document.createElement("div");
        row.className = "marquee-row";
        row.dataset.text = text;
        row.style.position = "relative";
        row.style.lineHeight = rowLineHeight;
        row.textContent = text;
        return row;
    }));

    box.dataset.originalMessage = normalizedMessage;
    box.dataset.best = normalizedMessage;
    originalMessageLayouts.delete(marquee);
    updateOriginalMessage();
    window.dispatchEvent(new Event("resize"));
}

function gameId() {
    return document.getElementById("tryItBox").dataset.gameId;
}

function cookieName(name) {
    // TryIt retains its original cookie names, so existing saved drafts and
    // suggestions still load. A game uses its id to isolate reused puzzles.
    return gameId() ? "game-" + gameId() + "+" + name : originalMessage() + "+" + name;
}

function updateTryItHint() {
    const box = document.getElementById("tryItBox");
    const hint = document.getElementById("tryItHint");
    if (hint) {
        hint.hidden = hintSeen("tryit") || box.textContent !== "" || document.activeElement === box;
    }
}

function initTryItHint() {
    const box = document.getElementById("tryItBox");
    const stage = box.closest(".composer-stage");
    if (!stage || document.getElementById("tryItHint")) {
        return;
    }
    const hint = document.createElement("div");
    hint.id = "tryItHint";
    hint.className = "tryit-hint";
    hint.dataset.hint = "tryit";
    hint.textContent = stage.dataset.hintText || "click here to start making your own message";
    hint.style.whiteSpace = "pre-line";
    hint.addEventListener("click", () => {
        markHintSeen("tryit");
        box.focus();
    });
    stage.appendChild(hint);
    ["focus", "blur", "input"].forEach((evt) => box.addEventListener(evt, updateTryItHint));
    updateTryItHint();
}

function initKeyboardAlignment() {
    const box = document.getElementById("tryItBox");
    const stage = document.querySelector(".marquee-stage");
    const vv = window.visualViewport;
    if (!box || !stage || !vv || !window.matchMedia("(pointer: coarse)").matches) {
        return;
    }
    const shell = document.querySelector(".site-shell") || document.body;
    const KEYBOARD_MIN_SHRINK = 120; // ignores browser URL-bar resizes
    let timer = null;
    let keyboardOpen = false;
    let baseline = vv.height;

    function align() {
        if (document.activeElement !== box || !keyboardOpen) {
            return;
        }
        shell.style.paddingBottom = Math.max(0, baseline - vv.height) + "px";
        const target = stage.querySelector(".marquee-message") || stage;
        const top = target.getBoundingClientRect().top + window.scrollY;
        window.scrollTo({ top: top, behavior: "smooth" });
    }

    function closeKeyboard() {
        keyboardOpen = false;
        clearTimeout(timer);
        shell.style.paddingBottom = "";
    }

    // Aligns only on the closed -> open keyboard transition, never on later resizes or scrolling.
    vv.addEventListener("resize", () => {
        if (document.activeElement !== box) {
            baseline = vv.height;
            return;
        }
        const shrunk = baseline - vv.height > KEYBOARD_MIN_SHRINK;
        if (shrunk && !keyboardOpen) {
            keyboardOpen = true;
            clearTimeout(timer);
            timer = setTimeout(align, 100);
            setTimeout(align, 450); // iOS applies its own scroll after the keyboard animates
        } else if (!shrunk && keyboardOpen) {
            closeKeyboard();
        }
    });
    box.addEventListener("focus", () => {
        if (!keyboardOpen) {
            baseline = vv.height;
        }
    });
    box.addEventListener("blur", () => {
        closeKeyboard();
        setTimeout(() => { baseline = vv.height; }, 400);
    });
}

function myInit() {
    initTryItHint();
    initKeyboardAlignment();
    const message = originalMessage();
    const saveResponse = document.getElementById("saveResponse");

    if (saveResponse) {
        saveResponse.innerHTML = "";
    }
    updateOriginalMessage(message);
    updateButtons();
    LoadDraftsFromCookie(cookieName("drafts"));
    updateDraftsSection();
    LoadSuggestionsFromCookie(cookieName("suggestions"));
    initializeGameTimer();
}

function updateOriginalMessage() {
    updateTryItBox(false);
    updateScrabbleSuggestions();
    updateVoteUrl();
    updateButtons();
}

function updateVoteUrl() {
    const voteLink = document.getElementById("href_vote");
    if (!voteLink) {
        return;
    }

    const voteUrl = new URL(voteLink.href, window.location.origin);
    if (gameId()) {
        voteUrl.searchParams.set("gameId", gameId());
    } else {
        voteUrl.searchParams.set("selection", originalMessage());
    }
    voteLink.href = voteUrl.toString();
}

function formatText(sentence, letters) {
    let remainingLetters = letters.toUpperCase();
    const upperSentence = sentence.toUpperCase();
    let output = "";

    for (let index = 0; index < upperSentence.length; index++) {
        const character = upperSentence[index];
        const escapedCharacter = character.replace(/[&<>"']/g, (match) => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[match]);

        if (remainingLetters.includes(character)) {
            output += escapedCharacter;
            remainingLetters = remainingLetters.replace(character, "");
        } else if (/[A-Z]/.test(character)) {
            output += `<span class="unavailable-letter" style="color: #c00 !important">${escapedCharacter}</span>`;
        } else {
            output += escapedCharacter;
        }
    }
    return output;
}

function unusedLetters(text, letters) {
    let usedLetters = text.toUpperCase().replaceAll(" ", "");
    const availableLetters = letters.toUpperCase().replaceAll(" ", "");
    let output = "";

    for (let index = 0; index < availableLetters.length; index++) {
        if (!usedLetters.includes(availableLetters[index])) {
            output += availableLetters[index];
        } else {
            usedLetters = usedLetters.replace(availableLetters[index], "");
        }
    }
    return output;
}

function updateOriginalMessageDisplay(letters, keepOrder = false) {
    const marquee = document.querySelector(".marquee-stage .marquee-message");
    if (!marquee) {
        return;
    }

    let layout = originalMessageLayouts.get(marquee);
    if (!layout) {
        // Measure only after the marquee font loads so the locked size is correct.
        if (document.fonts && document.fonts.status !== "loaded") {
            document.fonts.ready.then(() => updateTryItBox(false));
            return;
        }
        const rect = marquee.getBoundingClientRect();
        const rows = Array.from(marquee.querySelectorAll(".marquee-row"));
        const rowTexts = rows.map((row) => (row.firstChild ? row.firstChild.textContent : ""));
        const original = rowTexts.join("").split("");
        layout = {
            width: rect.width,
            height: rect.height,
            original,
            current: original.slice(),
            rows: rows.map((row, index) => ({
                element: row,
                capacity: rowTexts[index].length,
                height: row.getBoundingClientRect().height
            }))
        };
        originalMessageLayouts.set(marquee, layout);
        [marquee, document.getElementById("tryItBox").closest(".marquee-message")].forEach((frame) => {
            frame.style.boxSizing = "border-box";
            frame.style.width = `${layout.width}px`;
            frame.style.height = `${layout.height}px`;
            frame.style.maxWidth = "100%";
        });
        layout.rows.forEach(({ element, height }) => {
            element.style.minHeight = `${height}px`;
            element.style.whiteSpace = "pre-wrap";
        });
    }

    // Keep letters that are still available in their current slots; blank the rest.
    const counts = new Map();
    for (const letter of letters) {
        counts.set(letter, (counts.get(letter) || 0) + 1);
    }
    const isLetterSlot = (index) => layout.original[index] !== " ";
    layout.current = layout.current.map((character, index) => {
        if (!isLetterSlot(index) || character === " ") {
            return character;
        }
        const count = counts.get(character) || 0;
        if (count > 0) {
            counts.set(character, count - 1);
            return character;
        }
        return " ";
    });
    // Letters that came back go to their original slot first, then any blank slot.
    // With every letter back, restore the original order.
    if (!keepOrder && letters.length === layout.original.filter((c) => c !== " ").length) {
        layout.current = layout.original.slice();
        counts.clear();
    }
    counts.forEach((count, letter) => {
        for (; count > 0; count--) {
            let slot = layout.current.findIndex((c, i) => c === " " && layout.original[i] === letter);
            if (slot === -1) {
                slot = layout.current.findIndex((c, i) => c === " " && isLetterSlot(i));
            }
            if (slot !== -1) {
                layout.current[slot] = letter;
            }
        }
    });

    let offset = 0;
    layout.rows.forEach(({ element, capacity }) => {
        element.textContent = layout.current.slice(offset, offset + capacity).join("");
        offset += capacity;
    });
}

function hintSeen(name) {
    return getCookie("hint-" + name) === "1";
}

function resetHelp() {
    ["tryit", "draft", "word", "ai"].forEach((name) => setCookie("hint-" + name, "", -1));
    window.location.reload();
}

function markHintSeen(name) {
    setCookie("hint-" + name, "1", 3650);
    document.querySelectorAll('[data-hint="' + name + '"]').forEach((element) => element.remove());
}

function updateDraftsSection() {
    const drafts = document.getElementById("drafts");
    const section = drafts.closest(".saved-drafts");
    const hasDrafts = drafts.children.length > 0;
    section.hidden = !hasDrafts || document.body.dataset.gameEnded === "true";
    const hint = section.querySelector('[data-hint="draft"]');
    if (hint) {
        hint.hidden = !hasDrafts;
    }
}

function changeTryItBox(clickedElement) {
    if (clickedElement.closest("#aiSuggestions")) {
        markHintSeen("ai");
    } else {
        markHintSeen("draft");
    }
    document.getElementById("tryItBox").innerText = clickedElement.textContent;
    updateTryItBox(true);
    updateScrabbleSuggestions();
}

function insertWordSuggestion(clickedElement) {
    markHintSeen("word");
    const box = document.getElementById("tryItBox");
    const selection = window.getSelection();
    let range = selection.rangeCount ? selection.getRangeAt(0) : null;

    if (!range || !box.contains(range.startContainer) || !box.contains(range.endContainer)) {
        box.focus();
        range = document.createRange();
        range.selectNodeContents(box);
        range.collapse(false);
        selection.removeAllRanges();
        selection.addRange(range);
    }

    const caretRange = range.cloneRange();
    caretRange.selectNodeContents(box);
    caretRange.setEnd(range.startContainer, range.startOffset);
    const selectionStart = caretRange.toString().length;
    const selectionEnd = selectionStart + range.toString().length;
    const text = box.textContent;
    const prefix = text.slice(0, selectionStart).replace(/\s+$/, "");
    const suffix = text.slice(selectionEnd).replace(/^\s+/, "");
    const word = clickedElement.textContent.trim();
    const leftSpace = prefix ? " " : "";
    const rightSpace = suffix ? " " : "";

    box.textContent = prefix + leftSpace + word + rightSpace + suffix;
    const newCaretOffset = prefix.length + leftSpace.length + word.length;
    const newRange = document.createRange();
    const textNode = box.firstChild;
    newRange.setStart(textNode || box, textNode ? newCaretOffset : 0);
    newRange.collapse(true);
    selection.removeAllRanges();
    selection.addRange(newRange);

    updateTryItBox(true);
    updateScrabbleSuggestions();
}

document.addEventListener("keyup", function (event) {
    event.preventDefault();
    if (event.target.isContentEditable) {
        updateTryItBox(true);
        updateScrabbleSuggestions();
        updateButtons();
    }
});

function newMessageIsValid() {
    const text = document.getElementById("tryItBox").textContent.trim();
    if (text.length === 0 || text.toUpperCase() !== text) {
        return false;
    }

    const availableLetters = new Map();
    for (const letter of originalMessage().toUpperCase()) {
        if (/[A-Z]/.test(letter)) {
            availableLetters.set(letter, (availableLetters.get(letter) || 0) + 1);
        }
    }

    for (const letter of text) {
        if (!/[A-Z]/.test(letter)) {
            continue;
        }
        const count = availableLetters.get(letter) || 0;
        if (count === 0) {
            return false;
        }
        availableLetters.set(letter, count - 1);
    }
    return true;
}

function updateButtons() {
    if (document.body.dataset.gameEnded === "true") {
        return;
    }
    document.getElementById("saveDraft").disabled = !newMessageIsValid();
    document.getElementById("clearTryItBox").disabled =
        document.getElementById("tryItBox").textContent === "" && !marqueeIsScrambled();
}

function marqueeIsScrambled() {
    const marquee = document.querySelector(".marquee-stage .marquee-message");
    const layout = marquee && originalMessageLayouts.get(marquee);
    return !!layout && layout.current.some((c, i) => c !== " " && c !== layout.original[i]);
}

function updateTryItBox(fixCaret) {
    const box = document.getElementById("tryItBox");
    const text = box.textContent;
    let selection;
    let caretOffset;

    if (fixCaret) {
        selection = window.getSelection();
        if (selection.rangeCount !== 0) {
            const range = selection.getRangeAt(0);
            const textBeforeCaret = range.cloneRange();
            textBeforeCaret.selectNodeContents(box);
            textBeforeCaret.setEnd(range.startContainer, range.startOffset);
            caretOffset = textBeforeCaret.toString().length;
        }
    }

    box.innerHTML = formatText(text, originalMessage());

    if (fixCaret && caretOffset !== undefined) {
        const newRange = document.createRange();
        const walker = document.createTreeWalker(box, NodeFilter.SHOW_TEXT);
        let textNode = walker.nextNode();
        while (textNode && caretOffset > textNode.length) {
            caretOffset -= textNode.length;
            textNode = walker.nextNode();
        }
        if (textNode) {
            newRange.setStart(textNode, Math.min(caretOffset, textNode.length));
        } else {
            newRange.setStart(box, 0);
        }
        newRange.collapse(true);
        selection.removeAllRanges();
        selection.addRange(newRange);
    }

    updateOriginalMessageDisplay(unusedLetters(text, originalMessage()));
    updateButtons();
    updateTryItHint();
}

function saveAnswer(text) {
    return $.ajax({
        data: {
            answer: text,
            puzzle: originalMessage(),
            gameId: gameId()
        },
        type: "POST",
        url: "/save"
    });
}

// Submits each selected draft in order; stops at the first rejection.
function submitDrafts(drafts) {
    return drafts.reduce(function (chain, draft) {
        return chain.then(function () {
            return saveAnswer(draft).then(null, function (xhr) {
                return $.Deferred().reject(xhr, draft).promise();
            });
        });
    }, $.Deferred().resolve().promise());
}

// "single" = radio buttons, one submission; "multiple" = checkboxes.
const PICK_MODE = "single";

function currentDrafts() {
    return Array.from(document.querySelectorAll("#drafts .draft label")).map(function (label) { return label.textContent; });
}

function removeDraftByText(text) {
    const label = Array.from(document.querySelectorAll("#drafts .draft label")).find(function (item) { return item.textContent === text; });
    if (label) {
        label.parentElement.remove();
        SaveDraftsCookie(cookieName("drafts"));
        updateDraftsSection();
    }
}

function renderEndPanel(notice) {
    const panel = document.getElementById("endPanel");
    const drafts = currentDrafts();
    panel.innerHTML = "";

    const title = document.createElement("h1");
    title.className = "page-title";
    title.textContent = "Times Up!";
    panel.appendChild(title);

    if (notice) {
        const noticeLine = document.createElement("p");
        noticeLine.className = "notice-list";
        noticeLine.textContent = notice;
        panel.appendChild(noticeLine);
    }

    const message = document.createElement("p");
    message.className = "page-lede";
    panel.appendChild(message);

    if (drafts.length === 0) {
        message.textContent = notice
            ? "Oh snap!  Now you don't have any to submit.  Maybe next time."
            : "Oh no!  You didn't save any drafts!  Sorry, but you have to save at least one draft in a game to vote on a winner.";
        return;
    }
    message.textContent = drafts.length === 1
        ? "You only saved one draft.  That's OK...  click submit to submit it."
        : "Now it's time to pick your favorite one!";

    const inputType = PICK_MODE === "multiple" ? "checkbox" : "radio";
    const list = document.createElement("div");
    list.className = "choice-list";
    drafts.forEach(function (draft, index) {
        const row = document.createElement("div");
        row.className = "choice";
        const input = document.createElement("input");
        input.type = inputType;
        input.name = "pick";
        input.id = "pick-" + index;
        input.value = draft;
        input.checked = drafts.length === 1;
        input.addEventListener("change", updateSubmitState);
        const label = document.createElement("label");
        label.htmlFor = input.id;
        label.textContent = draft;
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "draftRemove";
        remove.textContent = "x";
        remove.addEventListener("click", function () {
            removeDraftByText(draft);
            renderEndPanel();
        });
        row.append(input, label, remove);
        list.appendChild(row);
    });
    panel.appendChild(list);

    const status = document.createElement("div");
    status.id = "endStatus";
    status.className = "help-label";
    const submit = document.createElement("button");
    submit.id = "submitPick";
    submit.type = "button";
    submit.className = "gold";
    submit.textContent = "Submit";
    submit.addEventListener("click", function () {
        const picked = Array.from(document.querySelectorAll("#endPanel input[name=pick]:checked")).map(function (input) { return input.value; });
        submit.disabled = true;
        status.textContent = "Submitting...";
        submitDrafts(picked).done(function () {
            window.location.href = "/vote/?gameId=" + encodeURIComponent(gameId());
        }).fail(function (xhr, draft) {
            if (xhr.status === 409) {
                removeDraftByText(draft);
                renderEndPanel("Someone beat you to that one!");
                return;
            }
            status.textContent = xhr.responseText || "Something went wrong submitting your draft.";
            updateSubmitState();
        });
    });
    const row = document.createElement("div");
    row.className = "button-row";
    row.appendChild(submit);
    panel.append(row, status);
    updateSubmitState();
}

function updateSubmitState() {
    const submit = document.getElementById("submitPick");
    if (submit) {
        submit.disabled = !document.querySelector("#endPanel input[name=pick]:checked");
    }
}

function updateScrabbleSuggestions() {
    const text = document.getElementById("tryItBox").textContent;

    $.ajax({
        data: {
            letters: unusedLetters(text, originalMessage())
        },
        type: "POST",
        url: "/scrabbler"
    }).done(function (data) {
        let html = data.trim();
        if (!html) {
            html = "No word suggestions";
        }
        if (html && !hintSeen("word")) {
            html = '<span data-hint="word">click a word to add it to your marquee<br></span>' + html;
        }
        document.getElementById("wordSuggestions").innerHTML = html;
    });
}

function updateAISuggestions() {
    if (document.body.dataset.gameEnded === "true") {
        return;
    }
    document.getElementById("aiSuggestions").innerHTML = "";
    document.getElementById("getAiSuggestions").hidden = true;
    startAnimation();

    $.ajax({
        data: {
            OriginalMessage: originalMessage(),
            gameId: gameId()
        },
        type: "POST",
        url: "/aisuggestions"
    }).done(function (data) {
        stopAnimation();
        document.getElementById("getAiSuggestions").hidden = false;
        document.getElementById("aiSuggestions").innerHTML = data;
        SaveAiSuggestionsCookie(cookieName("suggestions"));
        const aiBox = document.getElementById("aiSuggestions");
        if (!hintSeen("ai") && aiBox.querySelector("[onclick]")) {
            aiBox.insertAdjacentHTML("afterbegin", '<div data-hint="ai"><i>click a suggestion to add it to your marquee</i></div>');
        }
    });
}

function addDraftItem(draft) {
    draft = draft.trim().replace(/\xA0/g, " ").replace(/\s+/g, " ");

    const saveResponse = document.getElementById("saveResponse");
    if (currentDrafts().some(function (existing) { return existing.toUpperCase() === draft.toUpperCase(); })) {
        if (saveResponse) {
            saveResponse.textContent = "That draft is already in your list, so it was not added.";
        }
        return;
    }
    if (saveResponse) {
        saveResponse.textContent = "";
    }

    const label = document.createElement("label");
    label.textContent = draft;
    label.id = "label";

    const div = document.createElement("div");
    div.className = "draft";
    div.appendChild(label);
    div.append("  ");

    const removeButton = document.createElement("button");
    removeButton.innerHTML = "x";
    removeButton.className = "draftRemove";
    div.appendChild(removeButton);
    document.getElementById("drafts").appendChild(div);

    label.addEventListener("click", function () {
        changeTryItBox(this);
    });

    removeButton.addEventListener("click", function () {
        div.remove();
        SaveDraftsCookie(cookieName("drafts"));
        updateDraftsSection();
    });

    updateDraftsSection();
    clearTryItBox();
    SaveDraftsCookie(cookieName("drafts"));
}

// Countdown warning settings, in seconds remaining.
const TIMER_WARNING_SECONDS = 60;
const TIMER_BEEP_SECONDS = 30;

let beepContext = null;
let lastBeepSecond = null;

// Browsers only allow audio after a user gesture, so prepare the context on first interaction.
function prepareBeepContext() {
    if (!beepContext && (window.AudioContext || window.webkitAudioContext)) {
        beepContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (beepContext && beepContext.state === "suspended") {
        beepContext.resume();
    }
}
["pointerdown", "keydown", "touchstart"].forEach(function (name) {
    document.addEventListener(name, prepareBeepContext, { passive: true });
});

function playBeep() {
    if (!beepContext || beepContext.state !== "running") {
        return;
    }
    const oscillator = beepContext.createOscillator();
    const gain = beepContext.createGain();
    oscillator.frequency.value = 880;
    gain.gain.setValueAtTime(0.08, beepContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, beepContext.currentTime + 0.12);
    oscillator.connect(gain);
    gain.connect(beepContext.destination);
    oscillator.start();
    oscillator.stop(beepContext.currentTime + 0.12);
}

function initializeGameTimer() {
    const timer = document.getElementById("gameTimer");
    const endTime = document.body.dataset.gameEndTime;
    if (!timer || !endTime) {
        return;
    }

    const updateTimer = function () {
        const remainingMilliseconds = new Date(endTime).getTime() - Date.now();
        if (remainingMilliseconds <= 0) {
            timer.textContent = "Time remaining: 0:00";
            setGameEnded();
            return true;
        }
        const totalSeconds = Math.ceil(remainingMilliseconds / 1000);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        timer.textContent = "Time remaining: " + (hours ? hours + ":" + String(minutes).padStart(2, "0") : minutes) + ":" + String(seconds).padStart(2, "0");
        timer.classList.toggle("timer-low", totalSeconds <= TIMER_WARNING_SECONDS);
        if (totalSeconds <= TIMER_BEEP_SECONDS && totalSeconds !== lastBeepSecond) {
            lastBeepSecond = totalSeconds;
            playBeep();
        }
        return false;
    };
    if (updateTimer()) {
        return;
    }
    const timerInterval = window.setInterval(function () {
        if (updateTimer()) {
            window.clearInterval(timerInterval);
        }
    }, 1000);
}

function setGameEnded() {
    document.body.dataset.gameEnded = "true";
    document.querySelectorAll(".in-game-only").forEach(function (element) { element.hidden = true; });
    document.getElementById("tryItBox").contentEditable = "false";
    renderEndPanel();
    document.getElementById("endPanel").hidden = false;
}

function clearTryItBox() {
    const box = document.getElementById("tryItBox");
    box.textContent = "";
    updateTryItBox(true);
    box.focus();
    updateButtons();
    updateScrabbleSuggestions();
}

function clickScrambleOriginalMessage() {
    const marquee = document.querySelector(".marquee-stage .marquee-message");
    const layout = marquee && originalMessageLayouts.get(marquee);
    if (!layout) {
        return;
    }

    // Shuffle only the slots currently showing letters; blanks and word gaps stay put.
    const slots = [];
    layout.current.forEach((character, index) => {
        if (character !== " ") {
            slots.push(index);
        }
    });
    const letters = slots.map((index) => layout.current[index]);
    for (let index = letters.length - 1; index > 0; index--) {
        const otherIndex = Math.floor(Math.random() * (index + 1));
        [letters[index], letters[otherIndex]] = [letters[otherIndex], letters[index]];
    }
    slots.forEach((slot, index) => { layout.current[slot] = letters[index]; });
    updateOriginalMessageDisplay(letters.join(""), true);
    updateButtons();
}
