from datetime import datetime, timedelta, timezone
from sqlalchemy import DateTime, text, insert
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

class Votes(db.Model):
    __tablename__ = "votes"
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("Users", backref="users")
    answerId = db.Column(db.Integer, db.ForeignKey('answers.id'))

def vote_for_answer(userId, answerId):
    sql = f"INSERT INTO votes (userId, answerId) VALUES ({userId}, {answerId})"
    db.session.execute(text(sql))
    db.session.commit()
    #stmt = insert(Votes).values(userId=f"{userId}", answerId=f"{answerId}")
    #db.session.add(stmt)
    #db.session.commit()
    return

def save_answer_by_puzzle_text(answer_text, puzzle_text):
    #puzzles = Puzzles.query.where(Puzzles.text == puzzle_text).all()
    sql = f"select * from puzzles where puzzles.text = \"{puzzle_text}\";"
    puzzles = db.session.execute(text(sql)).all()

    if (len(puzzles) == 0):
        #save this new puzzle
        puzzle = Puzzles(text=puzzle_text)
        db.session.add(puzzle)
        db.session.commit()   

        #save this answer with new puzzle id
        answer = Answers(text=answer_text, puzzleId = puzzle.id)
        db.session.add(answer)
        db.session.commit()   
        return "Saved as new puzzle and answer!"
    if (len(puzzles) > 1):
        #something is wrong
        return "Something is wrong! There was more than one puzzle matched."
    else:
        #make sure this answer doesn't exist.
        #answers = Answers.query.where(Answers.text == answer_text).all()
        sql = f"select * from answers where answers.text = \"{answer_text}\";"
        answers = db.session.execute(text(sql)).all()
        if(len(answers) != 0):
            return "Answer already exists.  Not adding it."
        #make sure it is a valid answer.
        for letter in answer_text:
            if (letter not in puzzle_text):
                return "Not a vaid answer...  it has letters not in the puzzle. (extra spaces maybe?)"

        #save this answer with this puzzle id
        #answer = Answers(text=answer_text, puzzleId = puzzles[0].id)
        sql = f"INSERT INTO answers (puzzleId, text) VALUES ({puzzles[0].id}, \"{answer_text}\")"
        db.session.execute(text(sql))
        db.session.commit()        
        return "Added answer to existing puzzle."
    
def get_all_answers():
    sql = "SELECT answers.id as id, answers.text as answer, puzzles.text as puzzle, puzzles.id as puzzleId FROM answers left join puzzles on puzzles.id = answers.puzzleId order by puzzles.id;"
    return db.session.execute(text(sql)).all()

def get_answers(puzzleId):
    sql = f"SELECT puzzles.id as puzzleId, answers.id as answerId, puzzles.text as puzzle, answers.text as answer FROM answers left join puzzles on puzzles.id = answers.puzzleId where puzzles.id = {puzzleId} order by puzzles.id;"
    return db.session.execute(text(sql)).all()

def get_results():
    sql = "select puzzleId, answerId, puzzles.text, answers.text, count(answerId) from votes left join answers on answers.id = votes.answerId left join puzzles on puzzles.id = puzzleId group by answerId;"
    return db.session.execute(text(sql)).all()  

def get_results(puzzleId):
    sql = f"select answers.puzzleId, answers.id, answers.text, count(answerId) from answers left outer join votes on votes.answerId = answers.Id where answers.puzzleId = {puzzleId} group by answers.Id"
    return db.session.execute(text(sql)).all()

def get_puzzles_with_answers():
    sql = "select distinct(puzzles.id), puzzles.text from puzzles join answers on puzzles.id = answers.puzzleId;"
    return db.session.execute(text(sql)).all()
