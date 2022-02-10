from flask_restful.reqparse import Namespace

from db import db
from utils import _assign_if_something


class PermissionModel(db.Model):
    __tablename__ = 'permission'
    __table_args__ = {'schema': 'user'}

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(50), unique=True)

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def from_reqparse(self, newdata: Namespace):
        for no_pk_key in ['name']:
            _assign_if_something(self, newdata, no_pk_key)
