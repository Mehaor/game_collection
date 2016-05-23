from game_collection import db, User, SiteSetting
import settings


def init_db():
    db.drop_all()
    db.create_all()
    for user_data in settings.INITIAL_USERS:
        user = User(**user_data)
        db.session.add(user)
    for s in settings.INITIAL_SITE_SETTINGS:
        site_setting = SiteSetting(**s)
        db.session.add(site_setting)
    db.session.commit()

if __name__ == '__main__':
    init_db()