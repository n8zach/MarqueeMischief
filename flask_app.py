from marquee_mischief_openAI import message_to_messages
from marquee_helper import remove_punctuation, format_extra_letters
from json import decoder
from werkzeug.datastructures import MultiDict 
from flask import Flask, redirect, render_template, request, url_for, jsonify
from scrabble import suggest_words
from mm_game_db import save_answer_by_puzzle_text, get_results, get_all_answers, get_answers, get_puzzles_with_answers, vote_for_answer
from db import db
USE_PROXY = True
LOCAL = True

if(LOCAL):
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
        username="Gregor",
        password="gaspit",
        hostname="localhost",
        databasename="marquee_mischief",
    )
else:
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
        username="mischi3f",
        password="770Intermsnet",
        hostname="mischi3f.mysql.pythonanywhere-services.com",
        databasename="mischi3f$MarqueeMahem",
    )

app = Flask(__name__, template_folder='templates', static_url_path='/static')
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

with app.app_context():
    db.init_app(app) # to add the app inside SQLAlchemy()
    #db.create_all()

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

@app.route('/vote/', methods = ['POST', 'GET'])
def vote():
    if request.method == "GET":
        puzzles = get_puzzles_with_answers()
        return render_template("Vote.html", puzzles=puzzles, answers=[], selected=0)
    
    # POST
    # vote or choose puzzle?
    if(request.form.get("vote")):
        puzzles = get_puzzles_with_answers()
        vote_for_answer(userId=1, answerId=request.form["vote"])
        answers = get_results(request.form["selected"])
        return render_template("Vote.html", puzzles=puzzles, answers=answers, selected=request.form["selected"])
    elif(request.form.get("puzzles")):
        puzzles = get_puzzles_with_answers()
        answers = get_results(request.form["puzzles"])
        return render_template("Vote.html", puzzles=puzzles, answers=answers, selected=request.form["puzzles"])


@app.route('/test/', methods = ['POST', 'GET'])
def test():
    if request.method == "GET":
        answers = get_all_answers()
        results = get_results(9)
        return render_template("GameTest.html", answers=answers, results=results)
    
    # is this a vote?
    if(request.form.get("vote")):
        result = vote_for_answer(userId=1, answerId=request.form["vote"])
    # must be a save
    else:
        result = save_answer_by_puzzle_text(request.form["answer"], request.form["puzzle"])

    return redirect(url_for('test'))

@app.route('/', methods = ['GET'])
def default():
    return home()

@app.route('/save/', methods = ['POST'])
def save():
    result = save_answer_by_puzzle_text(request.form["answer"], request.form["puzzle"])
    return result


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
    close = [x for x in messages["bad"] if len(x["extra"]) == 1]

    out = []
    if(len(messages["good"]) == 0 and len(close) == 0):
        out.append("<b>I got no suggestions...  sorry :(")
    elif(len(messages["good"]) != 0):
        out.append("<b>Here are some suggestions:</b>")
        for g in messages["good"]:
            out.append(f'<div onclick="changeTryItBox(this)">{g["text"]}</div>')
    else:
        out.append("<b>I got nothin perfect.</b><br>")
    
    if(len(close) != 0):
        out.append("<br><b>These are close (Missing One Letter):</b>")
        for b in close:
            out.append(f'<div onclick="changeTryItBox(this)">{format_extra_letters(b["text"], message.upper())}</div>')
    elif(len(messages["good"]) != 0):
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

