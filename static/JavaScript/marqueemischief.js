window.addEventListener("load", myInit, true);

function originalMessage() {
    return document.getElementById("tryItBox").dataset.originalMessage;
}

function gameId() {
    return document.getElementById("tryItBox").dataset.gameId;
}

function cookieName(name) {
    // TryIt retains its original cookie names, so existing saved drafts and
    // suggestions still load. A game uses its id to isolate reused puzzles.
    return gameId() ? "game-" + gameId() + "+" + name : originalMessage() + "+" + name;
}

function myInit() {
    const message = originalMessage();
    const saveResponse = document.getElementById("saveResponse");

    document.getElementById("unusedLetters").innerHTML = unusedLetters(
        document.getElementById("tryItBox").dataset.best,
        message
    );
    if (saveResponse) {
        saveResponse.innerHTML = "";
    }
    updateOriginalMessage(message);
    updateButtons();
    LoadDraftsFromCookie(cookieName("drafts"));
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

function changeTryItBox(clickedElement) {
    document.getElementById("tryItBox").innerText = clickedElement.textContent;
    updateTryItBox(true);
    updateScrabbleSuggestions();
}

function insertWordSuggestion(clickedElement) {
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
        document.getElementById("tryItBox").textContent === "";
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

    document.getElementById("unusedLetters").innerHTML = unusedLetters(text, originalMessage());
    resizeTryItBox();
    updateButtons();
}

function resizeTryItBox() {
    const box = document.getElementById("tryItBox");
    if (!box) {
        return;
    }
    box.style.height = "auto";
    box.style.height = box.scrollHeight + "px";
}

window.addEventListener("resize", resizeTryItBox, { passive: true });

function saveAnswer(text) {
    document.getElementById("saveResponse").innerHTML = "Saving...";

    $.ajax({
        data: {
            answer: text,
            puzzle: originalMessage(),
            gameId: gameId()
        },
        type: "POST",
        url: "/save"
    }).done(function (data) {
        document.getElementById("saveResponse").innerHTML = data;
    });
}

function saveDraftAsAnswer(button) {
    saveAnswer(button.value);
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
        document.getElementById("wordSuggestions").innerHTML = data;
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
    });
}

function addDraftItem(draft) {
    draft = draft.trim().replace(/\xA0/g, " ").replace(/\s+/g, " ");

    const label = document.createElement("label");
    label.textContent = draft;
    label.id = "label";

    const div = document.createElement("div");
    div.className = "draft";
    div.appendChild(label);
    div.append("  ");

    const saveResponse = document.getElementById("saveResponse");
    let submitButton;
    if (saveResponse) {
        submitButton = document.createElement("button");
        submitButton.innerHTML = "submit";
        submitButton.value = draft;
        div.appendChild(submitButton);
        div.append("  ");
    }

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
    });

    if (submitButton) {
        submitButton.className = "draftSubmit";
        submitButton.addEventListener("click", function () {
            saveDraftAsAnswer(this);
            div.remove();
            SaveDraftsCookie(cookieName("drafts"));
        });
    }

    clearTryItBox();
    SaveDraftsCookie(cookieName("drafts"));
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
    document.getElementById("gameTimer").hidden = true;
    document.getElementById("href_vote").hidden = false;
    document.querySelectorAll(".draftSubmit, .draftRemove").forEach(function (button) { button.hidden = true; });
    document.getElementById("getAiSuggestions").disabled = true;
    document.getElementById("saveDraft").disabled = true;
    document.getElementById("clearTryItBox").disabled = true;
    document.getElementById("scrambleUnusedLetters").disabled = true;
    document.getElementById("tryItBox").contentEditable = "false";
}

function clearTryItBox() {
    const box = document.getElementById("tryItBox");
    box.textContent = "";
    updateTryItBox(true);
    box.focus();
    updateButtons();
    updateScrabbleSuggestions();
}

function clickScrambleUnusedLetters() {
    const letters = document.getElementById("unusedLetters").innerHTML.split("");

    for (let index = letters.length - 1; index > 0; index--) {
        const otherIndex = Math.floor(Math.random() * (index + 1));
        [letters[index], letters[otherIndex]] = [letters[otherIndex], letters[index]];
    }
    document.getElementById("unusedLetters").innerHTML = letters.join("");
}

function navigateToTryAnotherPuzzle(selector) {
    if (!selector.value) {
        return;
    }

    const tryItUrl = new URL(selector.dataset.tryitUrl, window.location.origin);
    tryItUrl.searchParams.set("OriginalMessage", selector.value);
    window.location.href = tryItUrl.toString();
}
