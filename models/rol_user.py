from flask_restful.reqparse import Namespace

from db import db
from utils import _assign_if_something


class RolUserModel(db.Model):
    __tablename__ = 'rol_user'
    __table_args__ = {'schema': 'user'}

    id = db.Column(db.BigInteger, primary_key=True)
    rol_id = db.Column(db.BigInteger, db.ForeignKey('user.rol.id'))
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.user.id'))

    def __init__(self, id, rol_id, user_id):
        self.id = id
        self.rol_id = rol_id
        self.user_id = user_id

    def json(self, jsondepth=0):
        return {
            'id': self.id,
            'rol_id': self.rol_id,
            'user_id': self.user_id,
        }

    @classmethod
    def find_by_rol_user_id(cls, id):
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
        for no_pk_key in ['rol_id', 'user_id']:
            _assign_if_something(self, newdata, no_pk_key)
