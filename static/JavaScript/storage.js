function setCookie(name, value, days) {
  var expires = "";
  if (days) {
      var date = new Date();
      date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
      expires = "; expires=" + date.toUTCString();
  }
  document.cookie = encodeURIComponent(name) + "=" + encodeURIComponent(value || "")  + expires + "; path=/";
}

function getCookie(name) {
  var nameEQ = encodeURIComponent(name) + "=";
  var ca = document.cookie.split(';');
  for(var i = 0; i < ca.length; i++) {
      var c = ca[i].trim();
      if (c.indexOf(nameEQ) == 0) {
          return decodeURIComponent(c.substring(nameEQ.length));
      }
  }
}

// Client-side data lives in localStorage; a long-lived cookie is the fallback
// when storage is unavailable (for example some private-browsing modes).
function storeSet(name, value) {
  try {
      localStorage.setItem(name, value);
  } catch (e) {
      setCookie(name, value, 365);
  }
}

function storeGet(name) {
  try {
      var value = localStorage.getItem(name);
      if (value !== null) {
          return value;
      }
  } catch (e) {
  }
  return getCookie(name);
}

function storeRemove(name) {
  try {
      localStorage.removeItem(name);
  } catch (e) {
  }
  setCookie(name, "", -1);
}

function loadDrafts(name)
{
    var drafts = [];
    try {
        drafts = JSON.parse(storeGet(name) || "[]");
    } catch (e) {
        return;
    }
    if (Array.isArray(drafts))
    {
        drafts.forEach(draft => {
            addDraftItem(draft);
        });
    }
}

function loadSuggestions(name)
{
    document.getElementById("aiSuggestions").innerHTML = storeGet(name) || "";
}

function saveDrafts(name)
{
    var drafts = Array.from(document.getElementsByClassName("draft")).map(draft => draft.firstChild.innerText);
    storeSet(name, JSON.stringify(drafts));
}

function saveAiSuggestions(name)
{
    storeSet(name, document.getElementById("aiSuggestions").innerHTML);
}
