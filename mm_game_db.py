from datetime import datetime, timedelta, timezone

from sqlalchemy import func, inspect, text
from db import db
from flask_login import UserMixin


def utc_now():
    return datetime.now(timezone.utc)


def utc_datetime(value):
    """Treat timestamps returned by MySQL as UTC when they are timezone-naive."""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


class Users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    password = db.Column(db.String(32))


class Puzzles(db.Model):
    __tablename__ = "puzzles"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(256))


class Games(db.Model):
    __tablename__ = "games"
    id = db.Column(db.Integer, primary_key=True)
    puzzleId = db.Column(db.Integer, db.ForeignKey("puzzles.id"), nullable=False)
    durationSeconds = db.Column(db.Integer, nullable=False)
    createdAt = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    startTime = db.Column(db.DateTime(timezone=True), nullable=True)


class Answers(db.Model):
    __tablename__ = "answers"
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("users.id"))
    puzzleId = db.Column(db.Integer, db.ForeignKey("puzzles.id"))
    gameId = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=True)
    text = db.Column(db.String(256))


class Votes(db.Model):
    __tablename__ = "votes"
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("users.id"))
    answerId = db.Column(db.Integer, db.ForeignKey("answers.id"))
    gameId = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=True)


def ensure_game_schema():
    """Add game references to databases created before the games feature."""
    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())
    statements = []
    if "answers" in existing_tables:
        columns = {column["name"] for column in inspector.get_columns("answers")}
        if "gameId" not in columns:
            statements.append("ALTER TABLE answers ADD COLUMN gameId INTEGER NULL")
    if "votes" in existing_tables:
        columns = {column["name"] for column in inspector.get_columns("votes")}
        if "gameId" not in columns:
            statements.append("ALTER TABLE votes ADD COLUMN gameId INTEGER NULL")
    for statement in statements:
        db.session.execute(text(statement))
    if statements:
        db.session.commit()


def get_or_create_puzzle(puzzle_text):
    puzzle_text = puzzle_text.strip().upper()
    puzzle = Puzzles.query.filter_by(text=puzzle_text).first()
    if puzzle is None:
        puzzle = Puzzles(text=puzzle_text)
        db.session.add(puzzle)
        db.session.commit()
    return puzzle


def create_game(puzzle_id, duration_seconds):
    game = Games(puzzleId=int(puzzle_id), durationSeconds=int(duration_seconds))
    db.session.add(game)
    db.session.commit()
    return game


def get_game(game_id):
    if not game_id:
        return None
    try:
        return db.session.get(Games, int(game_id))
    except (TypeError, ValueError):
        return None


def get_game_with_puzzle(game_id):
    game = get_game(game_id)
    if game is None:
        return None
    return (
        db.session.query(Games, Puzzles.text)
        .join(Puzzles, Puzzles.id == Games.puzzleId)
        .filter(Games.id == game.id)
        .first()
    )


def get_all_games():
    return (
        db.session.query(Games.id, Games.startTime, Puzzles.text, Games.durationSeconds)
        .join(Puzzles, Puzzles.id == Games.puzzleId)
        .order_by(Games.id.desc())
        .all()
    )


def get_unvoted_ended_games(user_id):
    games = (
        db.session.query(Games.id, Games.startTime, Puzzles.text, Games.durationSeconds)
        .join(Puzzles, Puzzles.id == Games.puzzleId)
        .outerjoin(Votes, (Votes.gameId == Games.id) & (Votes.userId == user_id))
        .filter(Votes.id.is_(None))
        .order_by(Games.id.desc())
        .all()
    )
    now = utc_now()
    return [
        game for game in games
        if game.startTime is not None
        and utc_datetime(game.startTime) + timedelta(seconds=game.durationSeconds) <= now
    ]


def start_game(game_id):
    game = get_game(game_id)
    if game is None:
        return None, "Game not found."
    if game.startTime is not None:
        return game, "This game has already started."
    game.startTime = utc_now()
    db.session.commit()
    return game, None


def game_end_time(game):
    if game is None or game.startTime is None:
        return None
    return utc_datetime(game.startTime) + timedelta(seconds=game.durationSeconds)


def game_has_ended(game, now=None):
    end_time = game_end_time(game)
    return end_time is not None and (now or utc_now()) >= end_time


def vote_for_answers(user_id, answer_ids, game_id):
    game = get_game(game_id)
    if game is None:
        return "Game not found."
    if not game_has_ended(game):
        return "Voting opens when this game's timer ends."
    if has_voted_in_game(user_id, game.id):
        return "You have already voted on this game."

    try:
        answer_ids = [int(answer_id) for answer_id in answer_ids]
    except (TypeError, ValueError):
        return "One or more selected answers are invalid."
    if len(set(answer_ids)) != 1:
        return "Choose exactly one answer."
    answers = Answers.query.filter(Answers.id.in_(answer_ids), Answers.gameId == game.id).all()
    answers_by_id = {answer.id: answer for answer in answers}
    if len(answers_by_id) != len(set(answer_ids)):
        return "One or more selected answers do not belong to this game."
    if any(answer.userId == user_id for answer in answers):
        return "You cannot vote for your own answer."

    db.session.add(Votes(userId=user_id, answerId=answer_ids[0], gameId=game.id))
    db.session.commit()
    return None


def has_voted_in_game(user_id, game_id):
    return db.session.query(Votes.id).filter_by(userId=user_id, gameId=game_id).first() is not None


def get_game_answer_votes(game_id):
    return (
        db.session.query(
            Answers.gameId,
            Answers.id,
            Answers.userId,
            Answers.text,
            func.count(Votes.id).label("count"),
        )
        .outerjoin(Votes, Votes.answerId == Answers.id)
        .filter(Answers.gameId == int(game_id))
        .group_by(Answers.id, Answers.gameId, Answers.userId, Answers.text)
        .order_by(func.count(Votes.id).desc(), Answers.id)
        .all()
    )


def save_answer_for_game(answer_text, game_id, user_id):
    game_and_puzzle = get_game_with_puzzle(game_id)
    if game_and_puzzle is None:
        return "Game not found."
    game, puzzle_text = game_and_puzzle
    if game.startTime is None:
        return "Waiting for the game master to start the game."
    if game_has_ended(game):
        return "The game has ended; answers can no longer be submitted."

    answer_text = " ".join(answer_text.replace("\xa0", " ").split()).upper()
    if not answer_text:
        return "New message is blank... nothing saved."
    if answer_text == puzzle_text:
        return "That's the same as the original message! Not adding it."
    for letter in answer_text:
        if letter != " " and letter not in puzzle_text:
            return "Not a valid message... it has letters not in the original message."
    if Answers.query.filter_by(gameId=game.id, text=answer_text).first() is not None:
        return "Answer already exists in this game. Not adding it."

    db.session.add(Answers(userId=user_id, puzzleId=game.puzzleId, gameId=game.id, text=answer_text))
    db.session.commit()
    return "New message added!"


def get_all_puzzles():
    return [(puzzle.id, puzzle.text) for puzzle in Puzzles.query.order_by(Puzzles.id).all()]


def get_game_user_votes(game_id):
    return db.session.execute(text("""
        SELECT puzzles.text AS puzzle, users.name AS user, COUNT(votes.id) AS votes
        FROM answers
        JOIN puzzles ON puzzles.id = answers.puzzleId
        JOIN users ON users.id = answers.userId
        LEFT JOIN votes ON votes.answerId = answers.id AND votes.gameId = answers.gameId
        WHERE answers.gameId = :game_id
        GROUP BY answers.gameId, users.name, puzzles.text
        ORDER BY users.name, votes DESC
    """), {"game_id": int(game_id)}).all()


def get_game_user_answer_votes(game_id):
    return db.session.execute(text("""
        SELECT puzzles.text AS puzzle, users.name AS user, answers.text AS answer, COUNT(votes.id) AS votes
        FROM answers
        JOIN puzzles ON puzzles.id = answers.puzzleId
        JOIN users ON users.id = answers.userId
        LEFT JOIN votes ON votes.answerId = answers.id AND votes.gameId = answers.gameId
        WHERE answers.gameId = :game_id
        GROUP BY answers.id, puzzles.text, users.name, answers.text
        ORDER BY votes DESC, answers.id
    """), {"game_id": int(game_id)}).all()


def get_game_results_text(game_id):
    text_out = '<table class="results-table"><thead><tr><th>Player</th><th>Votes</th></tr></thead><tbody>'
    for row in get_game_user_votes(game_id):
        text_out += f"<tr><td>{row[1]}</td><td>{row[2]}</td></tr>"
    text_out += '</tbody></table><table class="results-table"><thead><tr><th>Player</th><th>Message</th><th>Votes</th></tr></thead><tbody>'
    for row in get_game_user_answer_votes(game_id):
        text_out += f"<tr><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>"
    return text_out + "</tbody></table>"


def get_user_from_id(user_id):
    user = db.session.get(Users, int(user_id))
    return User(user.id, user.name, user.password) if user else None


def get_user_from_name_and_password(username, password):
    user = Users.query.filter_by(name=username, password=password).first()
    return User(user.id, user.name, user.password) if user else None


def add_user(username, password):
    if Users.query.filter_by(name=username).first() is not None:
        return False, "User already exists. Not adding it."
    db.session.add(Users(name=username, password=password))
    db.session.commit()
    return True, "success"
