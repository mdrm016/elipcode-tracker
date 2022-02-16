from flask_restful.reqparse import Namespace

from db import db
from utils import _assign_if_something


class TorrentCategoryModel(db.Model):
    __tablename__ = 'torrent_category'
    __table_args__ = {"schema": "torrent"}

    id = db.Column(db.BigInteger, primary_key=True)
    principal = db.Column(db.Boolean, nullable=False, default=False)
    torrent_id = db.Column(db.BigInteger, db.ForeignKey('torrent.torrent.id'))
    category_id = db.Column(db.BigInteger, db.ForeignKey('torrent.category.id'))

    def __init__(self, id, principal, torrent_id, category_id):
        self.id = id
        self.principal = principal
        self.torrent_id = torrent_id
        self.category_id = category_id

    def json(self, jsondepth=0):
        return {
            'id': self.id,
            'principal': self.principal,
            'torrent_id': self.torrent_id,
            'category_id': self.category_id,
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
        for no_pk_key in ['principal', 'torrent_id','category_id']:
            _assign_if_something(self, newdata, no_pk_key)

