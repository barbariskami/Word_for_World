from flask_sqlalchemy import SQLAlchemy
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class ModulesDB(db.Model):
    module_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=False, nullable=False)
    name = db.Column(db.String(60), unique=False, nullable=False)
    type = db.Column(db.String(60), unique=False, nullable=False)
    lang = db.Column(db.String(60), unique=False, nullable=False)

    def __repr__(self):
        return '<ModulesDB {} {} {}>'.format(
            self.module_id, self.user_id, self.name)


class WordsSets(db.Model):
    set_id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, unique=False, nullable=False)
    word1 = db.Column(db.String(60), unique=False, nullable=False)
    word2 = db.Column(db.String(350), unique=False, nullable=False)
    word3 = db.Column(db.String(60), unique=False, nullable=True)
    word4 = db.Column(db.String(60), unique=False, nullable=True)
    image = db.Column(db.String(100), unique=False, nullable=False)

    def __repr__(self):
        return '<WordsSets {} {} {} {} {}>'.format(
            self.module_id, self.word1, self.word2, self.word3, self.word4)


class InbuiltModule(db.Model):
    module_id = db.Column(db.Integer, primary_key=True)
    lang = db.Column(db.String(3), unique=False, nullable=False)
    name = db.Column(db.String(60), unique=False, nullable=False)
    type = db.Column(db.String(60), unique=False, nullable=False)

    def __repr__(self):
        return '<ModulesDB {} {} {} {}>'.format(
            self.module_id, self.name, self.type, self.lang)


class InbuiltSet(db.Model):
    set_id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, unique=False, nullable=False)
    word1 = db.Column(db.String(60), unique=False, nullable=False)
    word2 = db.Column(db.String(350), unique=False, nullable=False)
    word3 = db.Column(db.String(60), unique=False, nullable=True)
    word4 = db.Column(db.String(60), unique=False, nullable=True)
    image = db.Column(db.String(100), unique=False, nullable=False)

    def __repr__(self):
        return '<WordsSets {} {} {} {} {}>'.format(
            self.module_id, self.word1, self.word2, self.word3, self.word4)


db.create_all()
