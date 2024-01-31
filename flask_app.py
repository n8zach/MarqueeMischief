#from marquee_mischief_bing import message_to_messages
from marquee_mischief_openAI import message_to_messages
#from bing_helper import pick_funniest
from marquee_helper import remove_punctuation, format_extra_letters
from json import decoder
from werkzeug.datastructures import MultiDict 
from flask import Flask, redirect, render_template, request, url_for, jsonify
from scrabble import suggest_words

USE_PROXY = True

app = Flask(__name__, template_folder='templates', static_url_path='/static')



@app.route('/scrabbler/', methods = ['POST', 'GET'])
def scrabbler():
    if request.method == "POST":
        ret = ""
        letters = request.form['letters']
        suggestions = suggest_words(letters)
        if(len(suggestions) > 0):
            ret = "Some Suggestions:<br>" + ', '.join(suggestions)
        return ret
    else:
        return redirect(url_for('home'))

@app.route('/test/', methods = ['POST', 'GET'])
def test():
    if request.method == "GET":
        answers = ["one", "two", "three"]
        return render_template("GameTest.html", answers=answers)
    return redirect(url_for('test'))

@app.route('/')
def foo():
    return home()

@app.route('/home/', methods = ['POST', 'GET'])
def home():
    if request.method == 'GET':
        form_data = {}
        form_data["OriginalMessage"] = "PLEASE WAIT TO BE SEATED"
        form_data["Best"] = form_data["OriginalMessage"].replace("\n", "")
        return render_template('home.html', form_data = form_data)
    if request.method == 'POST':
        data = MultiDict([("OriginalMessage", request.form["OriginalMessage"].upper())])  
        return render_template('thinking.html', form_data = data)

@app.route('/thinking/', methods = ['POST', 'GET'])
def thinking():
    if request.method == 'GET':
        return redirect(url_for('home'))
    
    form_data = request.form
    message = form_data.getlist('OriginalMessage')[0]
    try:
        messages = message_to_messages(remove_punctuation(message), USE_PROXY)
    except decoder.JSONDecodeError as error:
        messages = error.doc
    except Exception as error:
        messages = f"An exception occurred: {error}"

    data = {}
    data["OriginalMessage"] = form_data.getlist('OriginalMessage')[0]
    out = []
    if(len(messages["good"]) != 0):
        out.append("<b>Here are some suggestions:</b>")
        for g in messages["good"]:
            out.append(f'<div onclick="changeTryItBox(this)">{g["text"]}</div>')
    else:
        out.append("<b>I got nothin perfect.</b><br>")
    
    close = [x for x in messages["bad"] if len(x["extra"]) == 1]
    if(len(close) != 0):
        out.append("<br><b>These are close (Missing One Letter):</b>")
        for b in close:
            out.append(f'<div onclick="changeTryItBox(this)">{format_extra_letters(b["text"], message.upper())}</div>')
    else:
        out.append("<b>I got nothin close.</b>")

    data["NewMessages"] = ''.join(out)
    
    if(len(messages["good"]) != 0):
        data["Best"] = messages["good"][0]["text"]
    else:
        data["Best"] = ""
    
    return render_template('home.html', form_data = data)

if __name__ == '__main__':
    app.run()

# god's goodness is not determined by your circumstances
# Toms nose is a booger mine

