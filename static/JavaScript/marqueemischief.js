window.addEventListener("load", myInit, true);

function originalMessage() {
    return document.getElementById("tryItBox").dataset.originalMessage;
}

function cookieName(name) {
    return originalMessage() + "+" + name;
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
    voteUrl.searchParams.set("selection", originalMessage());
    voteLink.href = voteUrl.toString();
}

function formatText(sentence, letters) {
    let remainingLetters = letters.toUpperCase();
    const upperSentence = sentence.toUpperCase();
    let output = "";

    for (let index = 0; index < upperSentence.length; index++) {
        if (remainingLetters.includes(upperSentence[index])) {
            output += upperSentence[index];
            remainingLetters = remainingLetters.replace(upperSentence[index], "");
        } else {
            output += upperSentence[index].toLowerCase();
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

document.addEventListener("keyup", function (event) {
    event.preventDefault();
    if (event.target.isContentEditable) {
        updateTryItBox(true);
        updateScrabbleSuggestions();
        updateButtons();
    }
});

function newMessageIsValid() {
    const text = document.getElementById("tryItBox").innerText.trim();
    return text.length > 0 && text.toUpperCase() === text;
}

function updateButtons() {
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
            caretOffset = selection.getRangeAt(0).startOffset;
        }
    }

    box.innerHTML = formatText(text, originalMessage());

    if (fixCaret && box.textContent.length !== 0) {
        const newRange = document.createRange();
        newRange.setStart(box.firstChild, caretOffset);
        newRange.collapse(true);
        selection.removeAllRanges();
        selection.addRange(newRange);
    }

    document.getElementById("unusedLetters").innerHTML = unusedLetters(text, originalMessage());
    updateButtons();
}

function saveAnswer(text) {
    document.getElementById("saveResponse").innerHTML = "Saving...";

    $.ajax({
        data: {
            answer: text,
            puzzle: originalMessage()
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
    document.getElementById("aiSuggestions").innerHTML = "";
    startAnimation();

    $.ajax({
        data: {
            OriginalMessage: originalMessage()
        },
        type: "POST",
        url: "/aisuggestions"
    }).done(function (data) {
        stopAnimation();
        document.getElementById("aiSuggestions").innerHTML = data;
        SaveAiSuggestionsCookie(cookieName("suggestions"));
    });
}

function addDraftItem(draft) {
    draft = draft.trim().replace(/\xA0/g, " ").replace(/\s+/g, " ");

    const label = document.createElement("label");
    label.innerHTML = draft;
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
        submitButton.addEventListener("click", function () {
            saveDraftAsAnswer(this);
            div.remove();
            SaveDraftsCookie(cookieName("drafts"));
        });
    }

    clearTryItBox();
    SaveDraftsCookie(cookieName("drafts"));
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