from datetime import datetime, timedelta, timezone
from sqlalchemy import DateTime, text
from db import db

class Users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    password = db.Column(db.String(32))

class Puzzles(db.Model):
    __tablename__ = "puzzles"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(256))
    start = db.Column(DateTime, default=datetime.utcnow())
    finish = db.Column(DateTime, default=datetime.utcnow() + timedelta(days=1))

class Answers(db.Model):    
    __tablename__ = "answers"
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("Users", backref="users")
    puzzleId = db.Column(db.Integer, db.ForeignKey('puzzles.id'))
    puzzle = db.relationship("Puzzles", backref="puzzles")
    text = db.Column(db.String(256))

def save_answer_by_puzzle_text(answer_text, puzzle_text):
    #check if this puzzle already exists
    #sql = "SELECT * FROM MY_TABLE WHERE text = {puzzle}"
    puzzles = Puzzles.query.where(Puzzles.text == puzzle_text).all()
    if (len(puzzles) == 0):
        #save this new puzzle
        puzzle = Puzzles(text=puzzle_text)
        db.session.add(puzzle)
        db.session.commit()   

        #save this answer with new puzzle id
        answer = Answers(text=answer_text, puzzleId = puzzle.id)
        db.session.add(answer)
        db.session.commit()   
        return
    if (len(puzzles) > 1):
        #something is wrong
        return
    else:
        #save this answer with this puzzle id
        answer = Answers(text=answer_text, puzzleId = puzzles[0].id)
        db.session.add(answer)
        db.session.commit()  
        return
    
def get_answers():
    sql = "SELECT answers.text as answer, puzzles.text as puzzle, puzzles.id FROM answers left join puzzles on puzzles.id = answers.puzzleId;"
    return db.session.execute(text(sql)).all()

