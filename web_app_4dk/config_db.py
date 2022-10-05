from flask_login import UserMixin

from web_app_4dk import db


class UserAuth(db.Model, UserMixin):
    """
    БД с данными пользователей
    """
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)