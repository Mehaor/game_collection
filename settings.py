DEBUG = False

SQLALCHEMY_DATABASE_URI = ''

INITIAL_USERS = []
INITIAL_SITE_SETTINGS = [
    {'name': 'current_game', 'value': ''}
]
DEFAULT_AVATAR_PATH = '/static/images/avatar.png'

APP_SECRET = ''

VK_APP_ID = ''
VK_APP_SECRET = ''
FB_APP_ID = ''

ADMIN_MODELS = [
    {'model': 'User', 'slug': 'user', 'editable': False, 'search_fields': ['username', 'screen_name']},
    {'model': 'Game', 'slug': 'game', 'editable': True, 'search_fields': ['title']},
    {'model': 'Gamsde', 'slug': 'game', 'editable': True},
]

try:
    from settings_local import *
except ImportError:
    pass

try:
    from settings_production import *
except ImportError:
    pass
