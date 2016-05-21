from flask import Flask, flash, jsonify, request, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import settings
import datetime
from functools import wraps
import json
import requests

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
            return redirect(url_for('login', next=request.url))
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
    #if request.method == 'POST':
    #    user = authenticate()
    #    if user:
    #        flash('logged in as %s' % user.name)
    #        session['user'] = user.__dict__
    #        print session['user']
    #        return redirect(redirect(request.args.get('next'))) if request.args.get('next') \
    #            else redirect(url_for('index'))
    return render_template('login.html', vk_app_id=settings.VK_APP_ID)


@app.route('/auth/', methods=['POST'])
def auth():
    if request.data:
        try:
            user = authenticate(json.loads(request.data))
            if user:
                return jsonify({'username': user.username,
                                'screen_name': user.screen_name,
                                'avatar': user.avatar
                                }), 200
        except ValueError:
            pass
    return 'auth failed', 403


def authenticate(auth_data):
    def auth_vk():
        if auth_data.get('authType') != 'vk':
            return None
        print type(auth_data)
        print auth_data.get('user')
        #r = requests.get('https://api.vk.com/method/users.get', params={'v': '5.52',
        #                                                                'user_ids': auth_data.get('user').get('id'),
        #                                                                'fields': 'photo_50'
        #                                                                })
        #print r.json()
        #try:
        #    avatar = r.json().get('response')[0].get('photo_50')
        #except (AttributeError, IndexError, KeyError):
        #    avatar = ''

        return {'username': 'vk%s' % auth_data.get('user').get('id'),
                'screen_name': '%s %s' % (auth_data.get('user').get('first_name'),
                                          auth_data.get('user').get('last_name')),
                #'avatar': avatar,
                }

    def auth_fb():
        return None

    def auth_anonymous():
        return None

    user_data = auth_vk() or auth_fb() or auth_anonymous()
    print user_data
    return User('username')

if __name__ == '__main__':
    app.run(debug=settings.DEBUG)
