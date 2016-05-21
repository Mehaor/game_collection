from flask import Flask, flash, jsonify, request, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import settings
import datetime
from functools import wraps
import json
import uuid


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

    @property
    def data(self):
        return {'username': self.username,
                'screen_name': self.screen_name or self.username,
                'avatar': self.avatar,
                'is_active': self.is_active,
                'is_admin': self.is_admin}

    @property
    def name(self):
        return self.screen_name or self.username

    @property
    def is_authenticated(self):
        return self.is_active


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    slug = db.Column(db.String(20), unique=True)
    picture = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.Date)
    is_published = db.Column(db.Boolean, default=False)

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


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user') is None or not session.get('user').get('is_active'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user') is None or not session.get('user').get('is_admin'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@login_required
def index():
    print User.query.all()
    return render_template('index.html')


@app.route('/admin/')
def admin():
    return ''


@app.route('/login/')
def login():
    if session.get('user'):
        return redirect(url_for('index'))
    return render_template('login.html', vk_app_id=settings.VK_APP_ID, fb_app_id=settings.FB_APP_ID)


@app.route('/logout/')
@login_required
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


@app.route('/auth/', methods=['POST'])
def auth():
    if request.data:
        try:
            user = authenticate(json.loads(request.data))
            if user:
                session['user'] = user.data
                d = user.data
                return jsonify(d), 200
        except ValueError:
            pass
    return 'auth failed', 403


def authenticate(auth_data):
    def auth_vk():
        if auth_data.get('authType') != 'vk':
            return None
        return {'username': 'vk%s' % auth_data.get('id'),
                'screen_name': '%s %s' % (auth_data.get('first_name'),
                                          auth_data.get('last_name')),
                'avatar': auth_data.get('photo_50')}

    def auth_fb():
        if auth_data.get('authType') != 'fb':
            return None
        print auth_data
        return {'username': 'fb%s' % auth_data.get('id'),
                'screen_name': auth_data.get('name'),
                'avatar': auth_data.get('picture', {}).get('data', {}).get('url')}

    def auth_anonymous():
        if auth_data.get('authType') != 'anonymous':
            return None
        print auth_data
        return {'username': auth_data.get('username') or 'anon%s' % str(uuid.uuid4())}

    user_data = auth_vk() or auth_fb() or auth_anonymous()
    print user_data
    if user_data:
        try:
            user = User(**user_data)
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            user = User.query.filter_by(username=user_data.get('username')).first()
        return user
    return None

app.secret_key = settings.APP_SECRET

if __name__ == '__main__':
    app.run(debug=settings.DEBUG)
