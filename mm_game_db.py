from datetime import datetime, timedelta, timezone
from sqlalchemy import DateTime, text, insert
from db import db
from flask_login import UserMixin

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

class Answers(db.Model):    
    __tablename__ = "answers"
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'))
    puzzleId = db.Column(db.Integer, db.ForeignKey('puzzles.id'))
    text = db.Column(db.String(256))

class Votes(db.Model):
    __tablename__ = "votes"
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'))
    answerId = db.Column(db.Integer, db.ForeignKey('answers.id'))

def vote_for_answer(userId, answerId):
    sql = f"INSERT INTO votes (userId, answerId) VALUES ({userId}, {answerId})"
    db.session.execute(text(sql))
    db.session.commit()

    return

def save_answer_by_puzzle_text(answer_text, puzzle_text, userId):
    sql = f"select * from puzzles where puzzles.text = \"{puzzle_text}\";"
    puzzles = db.session.execute(text(sql)).all()

    if (len(puzzles) == 0):
        #save this new puzzle
        sql = f"INSERT INTO puzzles (text) VALUES (\"{puzzle_text}\")"
        ret = db.session.execute(text(sql))
        db.session.commit()     

        #save this answer with new puzzle id
        sql = f"INSERT INTO answers (userId, puzzleId, text) VALUES ({userId}, {ret.lastrowid}, \"{answer_text}\")"
        db.session.execute(text(sql))
        db.session.commit()     
        return "Saved as new puzzle and answer!"
    if (len(puzzles) > 1):
        #something is wrong
        return "Something is wrong! There was more than one puzzle matched."
    else:
        #make sure this answer doesn't exist.
        sql = f"select * from answers where answers.text = \"{answer_text}\";"
        answers = db.session.execute(text(sql)).all()
        if(len(answers) != 0):
            return "Answer already exists.  Not adding it."
        #make sure it is a valid answer.
        for letter in answer_text:
            if (letter not in puzzle_text):
                return "Not a vaid answer...  it has letters not in the puzzle. (extra spaces maybe?)"

        #save this answer with this puzzle id
        sql = f"INSERT INTO answers (userId, puzzleId, text) VALUES ({userId}, {puzzles[0].id}, \"{answer_text}\")"
        db.session.execute(text(sql))
        db.session.commit()        
        return "Added answer to existing puzzle."
    
def is_password_correct(login):
    sql = f"SELECT password from users where name = '{login['name']}'"
    password = db.session.execute(text(sql)).all()
    if password.count == 0:
        return False
    
    if (login["password"] == password[0][0]):
        return True
    return False

def get_answerId_answer_puzzle_puzzleId():
    sql = "SELECT answers.id as id, answers.text as answer, puzzles.text as puzzle, puzzles.id as puzzleId FROM answers left join puzzles on puzzles.id = answers.puzzleId order by puzzles.id;"
    return db.session.execute(text(sql)).all()

def get_puzzleId_answerId_puzzle_answer(puzzleId):
    sql = f"SELECT puzzles.id as puzzleId, answers.id as answerId, puzzles.text as puzzle, answers.text as answer FROM answers left join puzzles on puzzles.id = answers.puzzleId where puzzles.id = {puzzleId} order by puzzles.id;"
    return db.session.execute(text(sql)).all()

def get_puzzleId_answerId_answer_votes(puzzleId):
    sql = f"select answers.puzzleId, answers.id, answers.text, count(answerId) as count from answers left outer join votes on votes.answerId = answers.Id where answers.puzzleId = {puzzleId} group by answers.Id order by count desc;"
    return db.session.execute(text(sql)).all()

def get_puzzles_that_have_answers():
    sql = "select distinct(puzzles.id), puzzles.text from puzzles join answers on puzzles.id = answers.puzzleId;"
    return db.session.execute(text(sql)).all()

def get_puzzle_user_answer_votes(puzzleId):
    sql = f"SELECT puzzles.text as puzzle, users.name as user, answers.text as answer, count(votes.id) as votes FROM answers left join puzzles on puzzles.id = answers.puzzleId left outer join users on users.Id = userId left outer join votes on votes.answerId = answers.id where puzzleId LIKE '{puzzleId}' group by answers.id order by puzzles.id, votes desc;"
    return db.session.execute(text(sql)).all()

def get_user_votes(puzzleId):
    sql = f"SELECT users.name as user, count(votes.id) as votes FROM answers left join puzzles on puzzles.id = answers.puzzleId join users on users.Id = userId left outer join votes on votes.answerId = answers.id where puzzleId LIKE '{puzzleId}' group by puzzleId, name order by user, puzzleId, votes desc;"
    return db.session.execute(text(sql)).all()

def get_user_from_id(userId):
    sql = f'SELECT * FROM users WHERE id = {userId};'
    user_data = db.session.execute(text(sql)).fetchone()
    if user_data:
        return User(*user_data)
    return None

def get_user_from_name_and_password(username, password):
    sql = f'SELECT * FROM users WHERE name = "{username}" AND password = "{password}";'
    user_data = db.session.execute(text(sql)).fetchone()
    if user_data:
        return User(*user_data)
    return None

def add_user(username, password):
    sql = f'select * from users where name = "{username}";'
    users = db.session.execute(text(sql)).all()
    if(len(users) != 0):
        return False, "User already exists.  Not adding it."
    sql = f'INSERT INTO users (name, password) VALUES ("{username}", "{password}");'
    db.session.execute(text(sql))
    db.session.commit()
    return True, "success"