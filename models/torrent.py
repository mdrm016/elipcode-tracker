import base64

from flask_restful.reqparse import Namespace

from db import db
from utils import _assign_if_something


class TorrentModel(db.Model):
    __tablename__ = 'torrent'
    __table_args__ = {'schema': 'torrent'}

    id = db.Column(db.BigInteger, primary_key=True)
    info_hash = db.Column(db.String)
    name = db.Column(db.String(300))
    description = db.Column(db.String)
    info = db.Column(db.PickleType)
    torrent_file_path = db.Column(db.String(300))
    uploaded_time = db.Column(db.DateTime)
    download_count = db.Column(db.Integer, default=0)
    seeders = db.Column(db.Integer, default=0)
    leechers = db.Column(db.Integer, default=0)
    last_checked = db.Column(db.DateTime)
    category_id = db.Column(db.Integer, db.ForeignKey('torrent.category.id'))
    user_create = db.Column(db.String(30))

    category = db.relationship('CategoryModel', backref='torrents')

    def __init__(self, id, info_hash, name, description, info, torrent_file, uploaded_time, download_count, seeders,
                 leechers, last_checked, category_id, user_create):
        self.id = id
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
        self.user_create = user_create

    def json(self, jsondepth=0):
        return {
            'id': self.id,
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
            'user_create': self.user_create,
        }

    @classmethod
    def find_by_torrent_id(cls, id):
        return cls.query.filter_by(id=id).first()

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
        for no_pk_key in ['info_hash', 'name', 'description', 'info', 'torrent_file', 'uploaded_time', 'download_count',
                          'seeders', 'leechers', 'last_checked', 'category_id', 'user_create']:
            _assign_if_something(self, newdata, no_pk_key)
