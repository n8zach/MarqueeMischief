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

def get_puzzle_id_from_text(puzzle_text):
    sql = f"select puzzles.id from puzzles where puzzles.text = \"{puzzle_text}\";"
    return db.session.execute(text(sql)).first()

def save_answer_by_puzzle_text(answer_text, puzzle_text, userId):
    if(len(answer_text) == 0):
        return "New message is blank...  nothing saved."
    
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
        return "Saved as new original message and new message!"
    if (len(puzzles) > 1):
        #something is wrong
        return "Something is wrong! There was more than one message matched."
    else:
        #make sure this answer doesn't exist.
        sql = f"select * from answers where answers.text = \"{answer_text}\";"
        answers = db.session.execute(text(sql)).all()
        if(len(answers) != 0):
            return "Answer already exists.  Not adding it."
        #make sure it is a valid answer.
        if (answer_text == puzzle_text):
            return "That's the same as the original message! Not adding it."
        for letter in answer_text:
            if (letter == " "):
                continue
            if (letter not in puzzle_text):
                return "Not a vaid message...  it has letters not in the origianl message."

        #save this answer with this puzzle id
        sql = f"INSERT INTO answers (userId, puzzleId, text) VALUES ({userId}, {puzzles[0].id}, \"{answer_text}\")"
        db.session.execute(text(sql))
        db.session.commit()        
        return "New message added!"
    
def is_password_correct(login):
    sql = f"SELECT password from users where name = '{login['name']}'"
    password = db.session.execute(text(sql)).all()
    if password.count == 0:
        return False
    
    if (login["password"] == password[0][0]):
        return True
    return False

def get_puzzle_text(puzzleId):
    sql = f'SELECT puzzles.text from puzzles where puzzles.id = "{puzzleId}"'
    return db.session.execute(text(sql)).first()[0]

def get_answerId_answer_puzzle_puzzleId():
    sql = "SELECT answers.id as id, answers.text as answer, puzzles.text as puzzle, puzzles.id as puzzleId FROM answers left join puzzles on puzzles.id = answers.puzzleId order by puzzles.id;"
    return db.session.execute(text(sql)).all()

def get_puzzleId_answerId_puzzle_answer(puzzleId):
    sql = f"SELECT puzzles.id as puzzleId, answers.id as answerId, puzzles.text as puzzle, answers.text as answer FROM answers left join puzzles on puzzles.id = answers.puzzleId where puzzles.id = {puzzleId} order by puzzles.id;"
    return db.session.execute(text(sql)).all()

def get_puzzleId_answerId_answer_votes(puzzleId):
    sql = f"select answers.puzzleId, answers.id, answers.text, count(answerId) as count from answers left outer join votes on votes.answerId = answers.Id where answers.puzzleId = {puzzleId} group by answers.Id order by count desc;"
    return db.session.execute(text(sql)).all()

def get_puzzleId_answerId_userId_answer_votes(puzzleId):
    sql = f"select answers.puzzleId, answers.id, answers.userId, answers.text, count(answerId) as count from answers left outer join votes on votes.answerId = answers.Id where answers.puzzleId = {puzzleId} group by answers.Id order by count desc;"
    return db.session.execute(text(sql)).all()

def get_puzzles_that_have_answers():
    sql = "select distinct(puzzles.id), puzzles.text from puzzles join answers on puzzles.id = answers.puzzleId;"
    return db.session.execute(text(sql)).all()

def get_puzzle_user_answer_votes(puzzleId):
    sql = f"SELECT puzzles.text as puzzle, users.name as user, answers.text as answer, count(votes.id) as votes FROM answers left join puzzles on puzzles.id = answers.puzzleId left outer join users on users.Id = userId left outer join votes on votes.answerId = answers.id where puzzleId LIKE '{puzzleId}' group by answers.id order by puzzles.id, votes desc;"
    return db.session.execute(text(sql)).all()

def get_puzzle_user_votes(puzzleId):
    sql = f"SELECT puzzles.text as puzzle, users.name as user, count(votes.id) as votes FROM answers left join puzzles on puzzles.id = answers.puzzleId join users on users.Id = userId left outer join votes on votes.answerId = answers.id where puzzleId LIKE '{puzzleId}' group by puzzleId, name order by puzzleId, user, votes desc;"
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

def delete_puzzle(puzzleId):
    sql = f'delete from votes where id > 0 and id IN (select vid FROM (select votes.id as vid from votes inner join answers on answers.id = votes.answerId inner join puzzles on puzzles.id = answers.puzzleId where puzzles.id = "{puzzleId}") as v);'
    db.session.execute(text(sql))
    db.session.commit()
    sql = f'delete from answers where id > 0 and id IN (select aid FROM (select answers.id as aid from answers inner join puzzles on puzzles.id = answers.puzzleId where puzzles.id = "{puzzleId}") as a);'
    db.session.execute(text(sql))
    db.session.commit()
    sql = f'delete from puzzles where puzzles.id = "{puzzleId}";'
    db.session.execute(text(sql))
    db.session.commit()

def get_results_text(puzzleId):
        data = get_puzzle_user_votes(puzzleId)
        puzzle = ""     
        text = '<table>'                        
        for row in data:
            if puzzle != row[0]: # new puzzle
                text += f'<tr><th colspan="2" nowrap>{row[0]}</th></tr>'
                puzzle = row[0]
            text += f'<tr><td>{row[1]}</td><td>{row[2]}</td></tr>'
            # end thetable
        text += '</table><br>'
        
        data = get_puzzle_user_answer_votes(puzzleId)
        puzzle = ""     
        text += '<table>'                        
        for row in data:
            if puzzle != row[0] and puzzleId == "%": # new puzzle
                text += f'<tr><th colspan="3">{row[0]}</th></tr>'
                puzzle = row[0]
            text += f'<tr><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>'

        # end thetable
        text += '</table>'
        return text