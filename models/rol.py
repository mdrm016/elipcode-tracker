from flask_restful.reqparse import Namespace

from db import db
from utils import _assign_if_something


class RolModel(db.Model):
    __tablename__ = 'rol'
    __table_args__ = {'schema': 'user'}

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(50), unique=True)

    def __init__(self, name=None):
        self.name = name

    def json(self, jsondepth=0):
        return {
            'id': self.id,
            'name': self.name,
        }

    @classmethod
    def find_by_rol_id(cls, id):
        return cls.query.filter_by(id=id).first()

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
        for no_pk_key in ['name']:
            _assign_if_something(self, newdata, no_pk_key)
