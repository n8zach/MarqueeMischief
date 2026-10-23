import os
from html import escape
from urllib.parse import parse_qs, urlsplit

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_migrate import Migrate
from werkzeug.exceptions import MethodNotAllowed, NotFound
from marquee_helper import remove_punctuation
from marquee_mischief_openAI import message_to_messages
from mm_game_db import (
    ANSWER_ADDED_MESSAGE,
    ANSWER_EXISTS_MESSAGE,
    add_user,
    create_game as create_game_record,
    game_end_time,
    game_has_ended,
    get_all_games,
    get_all_puzzles,
    get_game,
    get_game_answer_votes,
    get_game_results_text,
    get_game_submitter_and_voter_counts,
    get_games_participated,
    get_game_with_puzzle,
    get_or_create_puzzle,
    get_user_from_id,
    get_user_from_name_and_password,
    get_unvoted_ended_games,
    has_submitted_in_game,
    has_voted_in_game,
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
app.jinja_env.filters["marquee_row"] = lambda message, original=None: message_to_marquee_html(message, include_assets=False, like=original)
# Seconds between vote page refreshes; override with the VOTE_REFRESH_SECONDS environment variable.
app.config["VOTE_REFRESH_SECONDS"] = int(os.environ.get("VOTE_REFRESH_SECONDS", 30))

with app.app_context():
    db.init_app(app)
Migrate(app, db)

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


def _safe_next_url(next_url):
    try:
        parsed_url = urlsplit(next_url)
    except ValueError:
        return None
    if (
        not next_url.startswith("/")
        or next_url.startswith("//")
        or "\\" in next_url
        or parsed_url.scheme
        or parsed_url.netloc
        or any(ord(character) < 32 or ord(character) == 127 for character in next_url)
    ):
        return None
    try:
        endpoint, path_values = app.url_map.bind("localhost").match(parsed_url.path, method="GET")
    except (MethodNotAllowed, NotFound):
        return None
    query_values = {
        key: values
        for key, values in parse_qs(parsed_url.query, keep_blank_values=True).items()
        if key not in {"_anchor", "_external", "_method", "_scheme"} and key not in path_values
    }
    return url_for(endpoint, **query_values, **path_values)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = get_user_from_name_and_password(request.form["username"], request.form["password"])
        if user and get_user_from_id(user.id):
            login_user(user)
            return redirect(_safe_next_url(request.form.get("next_url", "")) or url_for("default"))
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
        result, message = add_user(
            request.form.get("username", ""),
            request.form.get("password", ""),
            request.form.get("authorization_code", ""),
        )
        if result:
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login", next=request.form.get("next", "")))
        flash(f"Registration failed. {message}", "error")
    return render_template("register.html")


@app.route("/scrabbler", methods=["POST"])
@login_required
def scrabbler():
    suggestions = suggest_words(request.form["letters"])
    clickable_suggestions = ', '.join(
        f'<span onmousedown="event.preventDefault()" onclick="insertWordSuggestion(this)">{escape(word)}</span>'
        for word in suggestions
    )
    return f"{clickable_suggestions}" if suggestions else "No word suggestions"


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
    puzzle_marquee = message_to_marquee_html(game[1]) if game else None
    return render_template("creategame.html", puzzles=get_all_puzzles(), game=game, game_url=game_url, puzzle_marquee=puzzle_marquee)


@app.route("/games/<int:game_id>/start", methods=["POST"])
@login_required
def start_created_game(game_id):
    game, error = start_game(game_id)
    if game is not None and game.startTime is not None and error:
        flash("Game already started.", "error")
        return redirect(url_for("create_game", gameId=game_id))
    flash(error or "Game started.", "error" if error else "success")
    return redirect(url_for("game", gameId=game_id))


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


def vote_block_reason(game, user_id):
    if game is None:
        return "Game not found."
    if game.startTime is None:
        return "This game hasn't started yet."
    if not game_has_ended(game):
        return "Voting opens when this game's timer ends."
    if not has_submitted_in_game(user_id, game.id):
        return "You didn't submit an answer in this game, so you can't vote on it."
    if has_voted_in_game(user_id, game.id):
        return "You have already voted on this game."
    return None


@app.route("/vote/", methods=["POST", "GET"])
@login_required
def vote():
    requested_game_id = request.values.get("gameId")
    if not requested_game_id:
        return render_template("Vote.html", votes=[], selected=None, block_reason="No game specified.")
    game = get_game(requested_game_id) if requested_game_id.isdigit() else None
    if game is None:
        return render_template("Vote.html", votes=[], selected=None, block_reason="Game not found.")
    original_message_html = ""
    game_and_puzzle = get_game_with_puzzle(game.id)
    original_message = game_and_puzzle[1] if game_and_puzzle else ""
    if game_and_puzzle:
        original_message_html = message_to_marquee_html(game_and_puzzle[1])
    block_reason = vote_block_reason(game, current_user.id)
    if block_reason:
        return render_template("Vote.html", votes=[], selected=game.id, original_message_html=original_message_html, block_reason=block_reason)

    if request.method == "POST" and request.form.getlist("vote[]"):
        error = vote_for_answers(current_user.id, request.form.getlist("vote[]"), game.id)
        if error:
            flash(error, "error")
        else:
            return redirect(url_for("results", gameId=game.id))
    answers = get_game_answer_votes(game.id)
    voteable_answers = [
        answer for answer in answers
        if answer[2] is None or int(answer[2]) != int(current_user.id)
    ]
    submitter_count = len({answer[2] for answer in answers if answer[2] is not None})
    return render_template(
        "Vote.html",
        votes=voteable_answers,
        submitter_count=submitter_count,
        refresh_seconds=app.config["VOTE_REFRESH_SECONDS"],
        selected=game.id,
        original_message_html=original_message_html,
        original_message=original_message,
        block_reason=None,
    )


@app.route("/results", methods=["GET"])
@login_required
def results():
    requested_id = request.args.get("gameId")
    if not requested_id:
        return render_template("results.html", games=get_games_participated(current_user.id), selected=None, game=None, notice=None)
    game_and_puzzle = get_game_with_puzzle(requested_id) if requested_id.isdigit() else None
    if game_and_puzzle is None:
        return render_template("results.html", games=None, selected=None, game=None, notice="Game not found.")
    game_record = game_and_puzzle[0]
    original_message_html = message_to_marquee_html(game_and_puzzle[1])
    if not has_submitted_in_game(current_user.id, game_record.id):
        return render_template("results.html", games=None, selected=game_record.id, game=None, original_message_html=original_message_html, notice="You did not participate in this game.")
    can_view = game_has_ended(game_record)
    submitter_count, voter_count = get_game_submitter_and_voter_counts(game_record.id)
    return render_template(
        "results.html",
        games=None,
        selected=game_record.id,
        game=game_and_puzzle,
        original_message_html=original_message_html,
        can_view_results=can_view,
        submitter_count=submitter_count,
        voter_count=voter_count,
        refresh_seconds=app.config["VOTE_REFRESH_SECONDS"],
        text=get_game_results_text(game_record.id) if can_view else "",
        notice=None,
    )


def _try_it_box_attrs(message, game_id=None):
    attrs = {
        "id": "tryItBox",
        "contenteditable": "true",
        "spellcheck": "false",
        "role": "textbox",
        "aria-label": "Your new message",
        "data-original-message": message,
        "data-best": message,
    }
    if game_id is not None:
        attrs["data-game-id"] = game_id
    return attrs


@app.route("/tryit/", methods=["GET"])
@login_required
def tryit():
    message = request.args.get("OriginalMessage", "PLEASE WAIT TO BE SEATED").upper()
    form_data = {"user": current_user.username, "OriginalMessage": message, "Best": message, "OriginalMessageDisplay": message_to_marquee_html(message), "TryItBoxDisplay": message_to_marquee_html(message, input_attrs=_try_it_box_attrs(message))}
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
    form_data = {"user": current_user.username, "OriginalMessage": puzzle_text, "Best": puzzle_text, "OriginalMessageDisplay": message_to_marquee_html(puzzle_text), "TryItBoxDisplay": message_to_marquee_html(puzzle_text, input_attrs=_try_it_box_attrs(puzzle_text, game_record.id))}
    game_url = url_for("game", gameId=game_record.id, _external=True)
    return render_template("game.html", form_data=form_data, game=game_record, end_time=utc_datetime(game_end_time(game_record)).isoformat(), game_has_ended=game_has_ended(game_record), game_url=game_url)


@app.route("/save", methods=["POST"])
@login_required
def save():
    message = save_answer_for_game(request.form.get("answer", ""), request.form.get("gameId"), current_user.id)
    if message == ANSWER_ADDED_MESSAGE:
        return message, 200
    return message, (409 if message == ANSWER_EXISTS_MESSAGE else 400)


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
