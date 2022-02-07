import base64

from flask_restful.reqparse import Namespace

from db import db
from utils import _assign_if_something


class PrincipalsModel(db.Model):
    __tablename__ = 'principals'

    principal_id = db.Column(db.Integer, primary_key=True)
    principal_name = db.Column(db.String, unique=True)

    def __init__(self, principal_id, principal_name=None):
        self.principal_id = principal_id
        self.principal_name = principal_name

    def json(self, jsondepth=0):
        return {
            'principal_id': self.principal_id,
            'principal_name': self.principal_name,
        }

    @classmethod
    def find_by_principal_id(cls, principal_id):
        return cls.query.filter_by(principal_id=principal_id).first()

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
        for no_pk_key in ['principal_name']:
            _assign_if_something(self, newdata, no_pk_key)

