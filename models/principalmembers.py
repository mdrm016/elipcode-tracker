import base64

from flask_restful.reqparse import Namespace

from db import db
from utils import _assign_if_something


class PrincipalmembersModel(db.Model):
    __tablename__ = 'principalmembers'

    principalmembership_id = db.Column(db.Integer, primary_key=True)
    principal_id = db.Column(db.Integer, db.ForeignKey('principals.principal_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))

    def __init__(self, principalmembership_id, principal_id, user_id):
        self.principalmembership_id = principalmembership_id
        self.principal_id = principal_id
        self.user_id = user_id

    def json(self, jsondepth=0):
        return {
            'principalmembership_id': self.principalmembership_id,
            'principal_id': self.principal_id,
            'user_id': self.user_id,
        }

    @classmethod
    def find_by_principalmembership_id(cls, principalmembership_id):
        return cls.query.filter_by(principalmembership_id=principalmembership_id).first()

    @classmethod
    def find_all(cls):
        return cls.query.all()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def from_reqparse(self, newdata: Namespace):
        for no_pk_key in ['principal_id','user_id']:
            _assign_if_something(self, newdata, no_pk_key)

