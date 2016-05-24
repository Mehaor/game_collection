# -*- coding: utf-8 -*-

from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
import settings
import datetime
from functools import wraps
import json
import uuid
import sys

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)


class DataMixin(object):
    REPR_FIELD_LIST = []
    FORM_DATA = []

    @property
    def data(self):
        return {attr: getattr(self, attr) for attr in self.REPR_FIELD_LIST}

    @property
    def data_list(self):
        return [getattr(self, attr) for attr in self.REPR_FIELD_LIST]


class User(db.Model, DataMixin):
    REPR_FIELD_LIST = ['id', 'username', 'screen_name', 'avatar', 'is_active', 'is_admin', 'created_at']

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(20), nullable=True)
    screen_name = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=True)

    def __init__(self, username, **kwargs):
        self.username = username
        self.password = kwargs.get('password', '')
        self.screen_name = kwargs.get('screen_name', '')
        self.avatar = kwargs.get('avatar', '')
        self.is_active = bool(kwargs.get('is_active', True))
        self.is_admin = bool(kwargs.get('is_admin', False))

    def __repr__(self):
        return '<User %r>' % self.username

    @property
    def name(self):
        return self.screen_name or self.username

    @property
    def is_authenticated(self):
        return self.is_active


class Game(db.Model, DataMixin):
    REPR_FIELD_LIST = ['id', 'title', 'description', 'slug', 'picture', 'created_at', 'is_published']
    FORM_DATA = [{'name': 'title', 'type': 'text'},
                 {'name': 'description', 'type': 'textarea'},
                 {'name': 'slug', 'type': 'text'},
                 {'name': 'picture', 'type': 'text'},
                 {'name': 'is_published', 'type': 'checkbox'}]

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    slug = db.Column(db.String(20), unique=True)
    picture = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())
    is_published = db.Column(db.Boolean, default=False)

    def __init__(self, title, description, slug, picture):
        self.title = title
        self.description = description
        self.slug = slug
        self.picture = picture
        self.is_published = False

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


def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user') and session.get('user').get('is_active'):
            return f(*args, **kwargs)
        return api_error(message='Login required', status=403)
    return decorated_function


def api_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user') and session.get('user').get('is_admin'):
            return f(*args, **kwargs)
        return api_error(message='Admin required', status=403)
    return decorated_function


@app.route('/')
@login_required
def index():
    return render_template('index.html')


def api_error(message=None, status=None):
    return jsonify({'error': message or ''}), 400 if not status or not isinstance(status, int) else status


@app.route('/admin/', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username'),
                                    password=request.form.get('password')).first()
        if user and user.is_admin:
            session['user'] = user.data
    if session.get('user', {}).get('is_admin'):
        return redirect(url_for('admin_main'))
    return render_template('admin.html')


@app.route('/admin/main/')
@admin_required
def admin_main():
    m_list = []
    for m in settings.ADMIN_MODELS:
        try:
            getattr(sys.modules[__name__], m.get('model'))
            m_list.append(m)
        except AttributeError:
            pass
    return render_template('admin.html', model_list=m_list)


@app.route('/admin/d/<model_slug>/')
def admin_model(model_slug):
    m = get_model_data(model_slug)
    return render_template('admin_model.html', model=m) if m else (render_template('404.html'), 404)


@app.route('/admin/d/<model_slug>/add/', methods=['GET', 'POST'])
@admin_required
def admin_add_model_object(model_slug):
    return add_edit_object(model_slug)


@app.route('/admin/d/<model_slug>/<int:pk>', methods=['GET', 'POST'])
@admin_required
def admin_view_model_object(model_slug, pk):
    try:
        cls = getattr(sys.modules[__name__], get_model_data(model_slug).get('model'))
        instance = cls.query.get(pk).data
        return render_template('admin_model_view.html', instance=instance)
    except AttributeError:
        return render_template('404.html'), 404


@app.route('/admin/d/<model_slug>/<int:pk>/edit/', methods=['GET', 'POST'])
@admin_required
def admin_edit_model_object(model_slug, pk):
    return add_edit_object(model_slug, pk)


def add_edit_object(model_slug, pk=None):
    try:
        cls = getattr(sys.modules[__name__], get_model_data(model_slug).get('model'))
        instance = {} if pk is None else cls.query.get(pk).data
    except AttributeError:
        return render_template('404.html'), 404
    if request.method == 'POST':
        if pk is None:
            o = cls(**{k: v for k, v in request.form.items()})
            try:
                db.session.add(o)
                db.session.commit()
            except IntegrityError:
                pass
        else:
            cls.query.filter_by(id=pk).update({k: v for k, v in request.form.items()})
            db.session.commit()
            o = cls.query.filter_by(id=pk).first()
        return redirect(url_for('admin_view_model_object', model_slug=model_slug, pk=o.id))
    form_data = cls.FORM_DATA
    for field_data in form_data:
        field_data['value'] = instance.get(field_data.get('name', ''), '')
    return render_template('admin_model_add.html', form_data=form_data)


@app.route('/admin/api/search/')
@api_admin_required
def api_admin_search():
    s = request.args.get('s')
    m = get_model_data(request.args.get('m', ''))
    if m:
        cl = getattr(sys.modules[__name__], m.get('model'))
        if s:
            d_list = cl.query.filter(or_(*[getattr(cl, f).startswith(s)
                                     for f in m.get('search_fields', []) if hasattr(cl, f)])).all()
        else:
            d_list = cl.query.all()[0:100]
        return jsonify({'items': [d.data_list for d in d_list],
                        'keys': d_list[0].REPR_FIELD_LIST if d_list else []})
    return api_error(message='Bad request', status=400)


def get_model_data(model_slug):
    for m in settings.ADMIN_MODELS:
        if m.get('slug') == model_slug:
            try:
                getattr(sys.modules[__name__], m.get('model'))
                return m
            except AttributeError:
                pass
    return None


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
                return jsonify(user.data), 200
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
        return {'username': 'fb%s' % auth_data.get('id'),
                'screen_name': auth_data.get('name'),
                'avatar': auth_data.get('picture', {}).get('data', {}).get('url')}

    def auth_anonymous():
        if auth_data.get('authType') != 'anonymous':
            return None
        return {'username': auth_data.get('username') or 'anon%s' % str(uuid.uuid4())}

    user_data = auth_vk() or auth_fb() or auth_anonymous()
    if user_data:
        user_data['is_admin'] = False
        if not user_data.get('avatar'):
            user_data['avatar'] = settings.DEFAULT_AVATAR_PATH
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
