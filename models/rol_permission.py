import base64

from flask_restful.reqparse import Namespace

from db import db
from utils import _assign_if_something


class RolPermissionModel(db.Model):
    __tablename__ = 'rol_permission'
    __table_args__ = {"schema": "user"}

    id = db.Column(db.BigInteger, primary_key=True)
    rol_id = db.Column(db.BigInteger, db.ForeignKey('user.rol.id'))
    permission_id = db.Column(db.BigInteger, db.ForeignKey('user.permission.id'))

    def __init__(self, id, rol_id, permission_id):
        self.id = id
        self.rol_id = rol_id
        self.permission_id = permission_id

    def json(self, jsondepth=0):
        return {
            'id': self.id,
            'rol_id': self.rol_id,
            'permission_id': self.permission_id,
        }

    @classmethod
    def find_by_id(cls, id):
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
        for no_pk_key in ['rol_id','permission_id']:
            _assign_if_something(self, newdata, no_pk_key)

