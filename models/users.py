import base64
import hashlib
import random
import string

from flask import current_app as app
from flask_restful.reqparse import Namespace
from flask_sqlalchemy import xrange

from db import db
from models.friendships import FriendshipsModel
from models.principalmembers import PrincipalmembersModel
from models.principals import PrincipalsModel
from utils import _assign_if_something


class UsersModel(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    email = db.Column(db.String, unique=True)
    passkey = db.Column(db.String)
    uploaded = db.Column(db.Integer, default=0)
    downloaded = db.Column(db.Integer, default=0)
    friendships = db.relationship(FriendshipsModel, primaryjoin=(FriendshipsModel.userone_id == user_id), backref='userone')
    awaiting_friendships = db.relationship(FriendshipsModel, primaryjoin=(FriendshipsModel.usertwo_id == user_id), backref='usertwo')
    principals = db.relationship(PrincipalsModel, secondary=PrincipalmembersModel.__tablename__)

    def __init__(self, username, password, email):
        self.username = username
        self.password = hashlib.sha1((password + app.config['USER_SECRET_KEY']).encode('utf-8')).hexdigest()
        self.email = email
        self.passkey = "".join([random.choice(string.ascii_letters) for x in xrange(16)])

    def json(self, jsondepth=0):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'password': self.password,
            'passkey': self.passkey,
            'uploaded': self.uploaded,
            'downloaded': self.downloaded,
        }

    @classmethod
    def find_by_user_id(cls, user_id):
        return cls.query.filter_by(user_id=user_id).first()

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
        for no_pk_key in ['username', 'password', 'passkey', 'uploaded', 'downloaded']:
            _assign_if_something(self, newdata, no_pk_key)
