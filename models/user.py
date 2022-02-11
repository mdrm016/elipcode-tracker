import base64
import hashlib
import random
import string

from flask import current_app as app
from flask_restful.reqparse import Namespace
from flask_sqlalchemy import xrange

from db import db
from models.friendships import FriendshipsModel
from models.rol_user import RolUserModel
from models.rol import RolModel
from utils import _assign_if_something


class UserModel(db.Model):
    __tablename__ = 'user'
    __table_args__ = {'schema': 'user'}

    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(300))
    email = db.Column(db.String(50), unique=True)
    passkey = db.Column(db.String(100))
    uploaded = db.Column(db.Integer, default=0)
    downloaded = db.Column(db.Integer, default=0)
    user_create = db.Column(db.String(30))
    date_create = db.Column(db.DateTime)

    friendships = db.relationship(FriendshipsModel, primaryjoin=(FriendshipsModel.userone_id == id), backref='userone')
    awaiting_friendships = db.relationship(FriendshipsModel, primaryjoin=(FriendshipsModel.usertwo_id == id),
                                           backref='usertwo')
    roles = db.relationship(RolModel, secondary='user.rol_user')

    def __init__(self, username, password, email, user_create, date_create):
        self.username = username
        self.password = hashlib.sha1((password + app.config['USER_SECRET_KEY']).encode('utf-8')).hexdigest()
        self.email = email
        self.passkey = "".join([random.choice(string.ascii_letters) for x in xrange(16)])
        self.user_create = user_create
        self.date_create = date_create

    def json(self, jsondepth=0):
        return {
            'user_id': self.id,
            'username': self.username,
            'password': self.password,
            'passkey': self.passkey,
            'uploaded': self.uploaded,
            'downloaded': self.downloaded,
            'user_create': self.user_create,
            'date_create': self.date_create,
        }

    @classmethod
    def find_by_user_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_all(cls):
        return cls.query.all()

    @classmethod
    def get_by_username_and_password(cls, username, password):
        pass_hash = hashlib.sha1((password + app.config['USER_SECRET_KEY']).encode('utf-8')).hexdigest()
        user = cls.query.filter_by(username=username, password=pass_hash).first()
        return user

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def from_reqparse(self, newdata: Namespace):
        for no_pk_key in ['username', 'password', 'passkey', 'uploaded', 'downloaded', 'user_create', 'date_create']:
            _assign_if_something(self, newdata, no_pk_key)
