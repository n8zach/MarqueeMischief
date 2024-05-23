function setCookie(name, value, days) {
  var expires = "";
  if (days) {
      var date = new Date();
      date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
      expires = "; expires=" + date.toUTCString();
  }
  document.cookie = name + "=" + (value || "")  + expires + "; path=/";
}

function getCookie(name) {
  var nameEQ = name + "=";
  var ca = document.cookie.split(';');
  for(var i = 0; i < ca.length; i++) {
      var c = ca[i];
      while (c.charAt(0) == ' ') {
          c = c.substring(1, c.length);
      }
      if (c.indexOf(nameEQ) == 0) {
          return c.substring(nameEQ.length, c.length);
      }
  }
}

function LoadDraftsFromCookie()
{
    drafts = getCookie("{{ form_data['OriginalMessage']}}+drafts").split("#");
    if(drafts.length == 1 && drafts[0] == '')
    {
        //none
        return;
    }
    drafts.forEach(draft => {
        addDraftItem(draft);
    });
}

function LoadSuggestionsFromCookie()
{
    suggestions = getCookie("{{ form_data['OriginalMessage']}}+suggestions");

    if (suggestions == undefined)
    {
        suggestions = ''
    }
    document.getElementById("aiSuggestions").innerHTML = suggestions;
}

function SaveDraftsCookie()
        {
            var drafts = "";
            Array.from(document.getElementsByClassName("draft")).forEach(draft => {
                drafts = drafts + draft.firstChild.innerText + "#";
             });

             setCookie("{{ form_data['OriginalMessage']}}+drafts", drafts.slice(0, -1));
        }

function SaveAiSuggestionsCookie()
{
    var suggestions =  document.getElementById("aiSuggestions").innerHTML;

        setCookie("{{ form_data['OriginalMessage']}}+suggestions", suggestions);
}