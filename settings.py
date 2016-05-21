SQLALCHEMY_DATABASE_URI = ''

INITIAL_USERS = []

INITIAL_SITE_SETTINGS = [
    {'name': 'current_game', 'value': ''}
]

DEBUG = False

APP_SECRET = ''

VK_APP_ID = ''
VK_APP_SECRET = ''

FB_APP_ID = ''

try:
    from settings_local import *
except ImportError:
    pass

try:
    from settings_production import *
except ImportError:
    pass
