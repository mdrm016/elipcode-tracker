from flask_restful.reqparse import Namespace

from db import db
from utils import _assign_if_something


class FriendshipsModel(db.Model):
    __tablename__ = 'friendships'
    __table_args__ = {'schema': 'user'}

    id = db.Column(db.Integer, primary_key=True)
    userone_id = db.Column(db.BigInteger, db.ForeignKey('user.user.id'))
    usertwo_id = db.Column(db.BigInteger, db.ForeignKey('user.user.id'))
    accepted = db.Column(db.Boolean)

    def __init__(self, id, userone_id, usertwo_id, accepted):
        self.id = id
        self.userone_id = userone_id
        self.usertwo_id = usertwo_id
        self.accepted = accepted

    def json(self, jsondepth=0):
        return {
            'id': self.id,
            'userone_id': self.userone_id,
            'usertwo_id': self.usertwo_id,
            'accepted': self.accepted,
        }

    @classmethod
    def find_by_friendship_id(cls, id):
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
        for no_pk_key in ['userone_id', 'usertwo_id', 'accepted']:
            _assign_if_something(self, newdata, no_pk_key)
