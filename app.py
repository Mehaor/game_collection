from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import settings
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(20), nullable=True)
    screen_name = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=True)

    def __init__(self, username, *args, **kwargs):
        self.username = username
        self.password = kwargs.get('password', '')
        self.screen_name = kwargs.get('screen_name', '')
        self.avatar = kwargs.get('avatar', '')
        self.is_active = bool(kwargs.get('is_active', True))
        self.is_admin = bool(kwargs.get('is_admin', True))

    def __repr__(self):
        return '<User %r>' % self.username


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    slug = db.Column(db.String(20), unique=True)
    picture = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.Date)

    def __init__(self, title, description, slug, picture):
        self.title = title
        self.description = description
        self.slug = slug
        self.picture = picture
        self.created_at = datetime.date.today()

    def __repr__(self):
        return '<Game> %r' % self.slug


class SiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    value = db.Column(db.String(200))




@app.route('/')
def index():
    print User.query.all()
    return User.query.all()[0].username


@app.route('/admin/')
def admin():
    return ''


if __name__ == '__main__':
    app.run(debug=settings.DEBUG)
