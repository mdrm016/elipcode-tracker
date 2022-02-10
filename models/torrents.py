import base64

from flask_restful.reqparse import Namespace

from db import db
from utils import _assign_if_something


class TorrentsModel(db.Model):
    __tablename__ = 'torrents'

    torrent_id = db.Column(db.Integer, primary_key=True)
    info_hash = db.Column(db.String)
    name = db.Column(db.String)
    description = db.Column(db.String)
    info = db.Column(db.PickleType)
    torrent_file = db.Column(db.String)
    uploaded_time = db.Column(db.DateTime)
    download_count = db.Column(db.Integer, default=0)
    seeders = db.Column(db.Integer, default=0)
    leechers = db.Column(db.Integer, default=0)
    last_checked = db.Column(db.DateTime)

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    category = db.relationship('CategoriesModel', backref='torrents')

    def __init__(self, torrent_id, info_hash, name, description, info, torrent_file, uploaded_time, download_count, seeders, leechers, last_checked, category_id):
        self.torrent_id = torrent_id
        self.info_hash = info_hash
        self.name = name
        self.description = description
        self.info = info
        self.torrent_file = torrent_file
        self.uploaded_time = uploaded_time
        self.download_count = download_count
        self.seeders = seeders
        self.leechers = leechers
        self.last_checked = last_checked
        self.category_id = category_id

    def json(self, jsondepth=0):
        return {
            'torrent_id': self.torrent_id,
            'info_hash': self.info_hash,
            'name': self.name,
            'description': self.description,
            'info': base64.b64encode(self.info).decode() if self.info else None,
            'torrent_file': self.torrent_file,
            'uploaded_time': self.uploaded_time,
            'download_count': self.download_count,
            'seeders': self.seeders,
            'leechers': self.leechers,
            'last_checked': self.last_checked,
            'category_id': self.category_id,
        }

    @classmethod
    def find_by_torrent_id(cls, torrent_id):
        return cls.query.filter_by(torrent_id=torrent_id).first()

    @classmethod
    def find_all(cls):
        return cls.query.all()

    def save_tmp(self):
        db.session.add(self)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def from_reqparse(self, newdata: Namespace):
        for no_pk_key in ['info_hash','name','description','info','torrent_file','uploaded_time','download_count','seeders','leechers','last_checked','category_id']:
            _assign_if_something(self, newdata, no_pk_key)

