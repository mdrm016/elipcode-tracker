import base64

from flask_restful.reqparse import Namespace

from db import db
from utils import _assign_if_something


class CategoriesModel(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String)
    name = db.Column(db.String)

    def __init__(self, id, image, name):
        self.id = id
        self.image = image
        self.name = name

    def json(self, jsondepth=0):
        return {
            'id': self.id,
            'image': self.image,
            'name': self.name,
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
        for no_pk_key in ['image','name']:
            _assign_if_something(self, newdata, no_pk_key)

