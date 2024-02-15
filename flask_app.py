import os
from marquee_mischief_openAI import message_to_messages
from marquee_helper import remove_punctuation, format_extra_letters
from json import decoder
from werkzeug.datastructures import MultiDict 
from flask import Flask, redirect, render_template, request, url_for, flash
from flask_login import LoginManager, login_manager, login_user, login_required, logout_user, UserMixin, current_user
from scrabble import suggest_words
from mm_game_db import add_user, get_user_from_id, get_user_from_name_and_password, save_answer_by_puzzle_text, get_puzzleId_answerId_answer_votes, get_puzzles_that_have_answers, vote_for_answer, get_puzzle_user_answer_votes
from db import db
from flask_migrate import Migrate

USE_PROXY = True

LOCAL = True
if (os.environ.get('PYTHONANYWHERE_SITE') != None):
    LOCAL = False

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
app.config['SECRET_KEY'] = 'TraLaLaa'
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

with app.app_context():
    db.init_app(app) # to add the app inside SQLAlchemy()
    #migrate = Migrate(app, db)
    #db.create_all()

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
     return get_user_from_id(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        next_url = request.form.get("next")

        user = get_user_from_name_and_password(username, password) 
        if user:
            login_user(user)
            flash('Login successful!', 'success')
            if(next_url):
                return redirect(next_url)
            return redirect(url_for('solo'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout successful!', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        result, message = add_user(request.form['username'], request.form['password'])
        if result:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash(f'Registration failed. {message}', 'error')
 
    return render_template('register.html')

@app.route('/scrabbler', methods = ['POST', 'GET'])
@login_required
def scrabbler():
    if request.method == "POST":
        ret = ""
        letters = request.form['letters']
        suggestions = suggest_words(letters)
        if(len(suggestions) > 0):
            ret = "Word Suggestions:<br>" + ', '.join(suggestions)
        return ret
    else:
        return redirect(url_for('solo'))

@app.route('/vote/', methods = ['POST', 'GET'])
@login_required
def vote():
    if request.method == "GET":
        puzzles = get_puzzles_that_have_answers()
        return render_template("Vote.html", puzzles=puzzles, votes=[], selected=0)
    
    # POST
    # vote or choose puzzle?
    if(request.form.get("vote")):
        puzzles = get_puzzles_that_have_answers()
        vote_for_answer(userId=1, answerId=request.form["vote"])
        votes = get_puzzleId_answerId_answer_votes(request.form["selected"])
        return render_template("Vote.html", puzzles=puzzles, votes=votes, selected=request.form["selected"])
    elif(request.form.get("puzzles")):
        puzzles = get_puzzles_that_have_answers()
        votes = get_puzzleId_answerId_answer_votes(request.form["puzzles"])
        return render_template("Vote.html", puzzles=puzzles, votes=votes, selected=request.form["puzzles"])


@app.route('/test/', methods = ['POST', 'GET'])
def test():
    if request.method == "GET":
        data = get_puzzle_user_answer_votes("%")
        puzzle = ""     
        text = '<table class="table">'
                        
        for row in data:
            if puzzle != row[0]: # new puzzle
                text += f'<tr><th td colspan="2">{row[0]}</th></tr>'
                puzzle = row[0]
            text += f'<tr><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>'

        # end thetable
        text += '</table>'
        return render_template("GameTest.html", text=text)

@app.route('/', methods = ['GET'])
@login_required
def default():
    return solo()

@app.route('/save', methods = ['POST'])
@login_required
def save():
    result = save_answer_by_puzzle_text(request.form["answer"], request.form["puzzle"], current_user.id)
    return result


@app.route('/solo', methods = ['POST', 'GET'])
@login_required
def solo():
    if request.method == 'GET':
        form_data = {}
        form_data["user"] = current_user.username
        form_data["OriginalMessage"] = "PLEASE WAIT TO BE SEATED"
        form_data["Best"] = form_data["OriginalMessage"]
        if request.args.get("NewOriginalMessage"):
            form_data["OriginalMessage"] = request.args["NewOriginalMessage"]
            form_data["Best"] = form_data["OriginalMessage"]
        return render_template('solo.html', form_data = form_data)

    if request.method == 'POST':
        form_data = request.form
        data = MultiDict([("OriginalMessage", form_data["OriginalMessage"].upper())])  
        return render_template('thinking.html', form_data = data)

@app.route('/thinking', methods = ['POST', 'GET'])
@login_required
def thinking():
    if request.method == 'GET':
        return redirect(url_for('solo'))
    
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
        out.append("<b>I got no suggestions...  sorry :(</b>")
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
    
    return render_template('solo.html', form_data = data)

if __name__ == '__main__':
    #app.run(host='192.168.1.78', port=5000, debug=True, threaded=False)
    app.run()
