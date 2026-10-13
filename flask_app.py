import os

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from marquee_helper import remove_punctuation
from marquee_mischief_openAI import message_to_messages
from mm_game_db import (
    add_user,
    create_game as create_game_record,
    ensure_game_schema,
    game_end_time,
    game_has_ended,
    get_all_games,
    get_all_puzzles,
    get_game,
    get_game_answer_votes,
    get_game_results_text,
    get_game_with_puzzle,
    get_or_create_puzzle,
    get_user_from_id,
    get_user_from_name_and_password,
    save_answer_for_game,
    start_game,
    utc_datetime,
    vote_for_answers,
)
from db import db
from original_message_display import message_to_marquee_html
from scrabble import suggest_words

USE_PROXY = True
LOCAL = os.environ.get("PYTHONANYWHERE_SITE") is None

if LOCAL:
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
        username="Gregor", password="gaspit", hostname="localhost", databasename="marquee_mischief"
    )
else:
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
        username="mischi3f", password="770Intermsnet", hostname="mischi3f.mysql.pythonanywhere-services.com", databasename="mischi3f$MarqueeMahem"
    )

app = Flask(__name__, template_folder="templates", static_url_path="/static")
app.config["SECRET_KEY"] = "TraLaLaa"
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

with app.app_context():
    db.init_app(app)
    db.create_all()
    ensure_game_schema()

login_manager = LoginManager(app)
login_manager.login_view = "login"


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", message="Page not found."), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return render_template("error.html", message="That request method is not allowed."), 405


@login_manager.user_loader
def load_user(user_id):
    return get_user_from_id(user_id)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = get_user_from_name_and_password(request.form["username"], request.form["password"])
        if user:
            login_user(user)
            return redirect(url_for("default"))
        flash("Login failed. Please check your username and password.", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        result, message = add_user(request.form["username"], request.form["password"])
        if result:
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        flash(f"Registration failed. {message}", "error")
    return render_template("register.html")


@app.route("/scrabbler", methods=["POST"])
@login_required
def scrabbler():
    suggestions = suggest_words(request.form["letters"])
    return "Word Suggestions:<br>" + ", ".join(suggestions) if suggestions else ""


@app.route("/aisuggestions", methods=["POST"])
@login_required
def aisuggestions():
    requested_game = get_game(request.form.get("gameId"))
    if requested_game and game_has_ended(requested_game):
        return "This game has ended; AI suggestions are no longer available.", 409
    message = request.form.get("OriginalMessage", "")
    try:
        messages = message_to_messages(remove_punctuation(message), USE_PROXY)
    except Exception as error:
        messages = {"good": [], "bad": [], "assistant": f"An exception occurred: {error}"}

    out = []
    if messages["good"]:
        out.append("<b>Suggestions:</b><br>")
        out.extend(f'<div onclick="changeTryItBox(this)">{item["text"]}</div>' for item in messages["good"])
    close = [item for item in messages["bad"] if len(item.get("extra", [])) == 1]
    if close:
        out.append("<br><b>These are close (Missing One Letter):</b><br>" if messages["good"] else "<b>I have no perfect suggestions, but these are close:</b><br>")
        out.extend(f'<div onclick="changeTryItBox(this)">{item["text"]}</div>' for item in close)
    if not out:
        out = ["<b>I have no suggestions... sorry :(</b>"]
    return "".join(out) + "<br><br>" + messages.get("assistant", "")


@app.route("/creategame/", methods=["GET", "POST"])
@login_required
def create_game():
    if request.method == "POST":
        puzzle_text = request.form.get("newPuzzle", "").strip()
        puzzle_id = request.form.get("puzzleId")
        try:
            hours = int(request.form.get("hours", "0"))
            minutes = int(request.form.get("minutes", "0"))
            duration_seconds = (hours * 60 + minutes) * 60
            if hours < 0 or not 0 <= minutes <= 59 or duration_seconds <= 0:
                raise ValueError
            if puzzle_text:
                puzzle = get_or_create_puzzle(puzzle_text)
            elif puzzle_id:
                puzzle = next((p for p in get_all_puzzles() if p[0] == int(puzzle_id)), None)
                if puzzle is None:
                    raise ValueError
                puzzle = get_or_create_puzzle(puzzle[1])
            else:
                raise ValueError
        except ValueError:
            flash("Choose an original message (or enter a new one) and a duration greater than zero.", "error")
            return render_template("creategame.html", puzzles=get_all_puzzles(), game=None)
        game = create_game_record(puzzle.id, duration_seconds)
        return redirect(url_for("create_game", gameId=game.id))

    game = get_game_with_puzzle(request.args.get("gameId")) if request.args.get("gameId") else None
    game_url = url_for("game", gameId=game[0].id, _external=True) if game else None
    return render_template("creategame.html", puzzles=get_all_puzzles(), game=game, game_url=game_url)


@app.route("/games/<int:game_id>/start", methods=["POST"])
@login_required
def start_created_game(game_id):
    _, error = start_game(game_id)
    flash(error or "Game started.", "error" if error else "success")
    return redirect(url_for("tryit", gameId=game_id))


@app.route("/game-status/<int:game_id>")
@login_required
def game_status(game_id):
    game = get_game(game_id)
    if game is None:
        return jsonify({"error": "Game not found."}), 404
    end_time = game_end_time(game)
    return jsonify({
        "started": game.startTime is not None,
        "ended": game_has_ended(game),
        "endTime": end_time.isoformat() if end_time else None,
    })


@app.route("/vote/", methods=["POST", "GET"])
@login_required
def vote():
    games = get_all_games()
    selected = request.values.get("gameId") or (str(games[0][0]) if games else None)
    game = get_game(selected)
    if game is None:
        return render_template("Vote.html", games=games, votes=[], selected=None, can_vote=False)
    if request.method == "POST" and request.form.getlist("vote[]"):
        error = vote_for_answers(current_user.id, request.form.getlist("vote[]"), game.id)
        flash(error or "Your vote was saved.", "error" if error else "success")
    return render_template("Vote.html", games=games, votes=get_game_answer_votes(game.id), selected=game.id, can_vote=game_has_ended(game))


@app.route("/results", methods=["GET"])
@login_required
def results():
    games = get_all_games()
    requested_id = request.args.get("gameId") or (str(games[0][0]) if games else None)
    game_and_puzzle = get_game_with_puzzle(requested_id) if requested_id else None
    selected = game_and_puzzle[0].id if game_and_puzzle else None
    return render_template(
        "results.html",
        games=games,
        selected=int(selected) if selected else None,
        game=game_and_puzzle,
        can_view_results=game_has_ended(game_and_puzzle[0]) if game_and_puzzle else False,
        text=get_game_results_text(selected) if game_and_puzzle and game_has_ended(game_and_puzzle[0]) else "",
    )


@app.route("/tryit/", methods=["GET"])
@login_required
def tryit():
    message = request.args.get("OriginalMessage", "PLEASE WAIT TO BE SEATED").upper()
    form_data = {"user": current_user.username, "OriginalMessage": message, "Best": message, "OriginalMessageDisplay": message_to_marquee_html(message)}
    return render_template("tryit.html", form_data=form_data, puzzles=get_all_puzzles())


@app.route("/game/", methods=["GET"])
@login_required
def game():
    game_id = request.args.get("gameId")
    if not game_id:
        return render_template("error.html", message="No game ID specified."), 400

    game_and_puzzle = get_game_with_puzzle(game_id)
    if game_and_puzzle is None:
        return render_template("error.html", message="Game not found."), 404
    game_record, puzzle_text = game_and_puzzle
    if game_record.startTime is None:
        return render_template("game_waiting.html", game=game_record)
    form_data = {"user": current_user.username, "OriginalMessage": puzzle_text, "Best": puzzle_text, "OriginalMessageDisplay": message_to_marquee_html(puzzle_text)}
    return render_template("game.html", form_data=form_data, game=game_record, end_time=utc_datetime(game_end_time(game_record)).isoformat(), game_has_ended=game_has_ended(game_record))


@app.route("/save", methods=["POST"])
@login_required
def save():
    return save_answer_for_game(request.form.get("answer", ""), request.form.get("gameId"), current_user.id)


@app.route("/", methods=["GET"])
def default():
    return render_template("home.html")


@app.route("/coming-soon/", methods=["GET"])
def coming_soon():
    return render_template("coming_soon.html")


@app.route("/test/", methods=["POST", "GET"])
def test():
    return render_template("GridTest.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
