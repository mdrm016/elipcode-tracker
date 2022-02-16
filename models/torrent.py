import base64

from flask_restful.reqparse import Namespace

from db import db
from models.category import CategoryModel
from models.torrent_category import TorrentCategoryModel
from models.torrent_file import TorrentFileModel
from utils import _assign_if_something


class TorrentModel(db.Model):
    __tablename__ = 'torrent'
    __table_args__ = {'schema': 'torrent'}

    id = db.Column(db.BigInteger, primary_key=True)
    info_hash = db.Column(db.String)
    name = db.Column(db.String(300))
    url = db.Column(db.String)
    description = db.Column(db.String)
    info = db.Column(db.PickleType)
    uploaded_time = db.Column(db.DateTime)
    download_count = db.Column(db.Integer, default=0)
    downloaded = db.Column(db.BigInteger, default=0)
    seeders = db.Column(db.Integer, default=0)
    leechers = db.Column(db.Integer, default=0)
    last_checked = db.Column(db.DateTime)
    user_create = db.Column(db.String(30))

    categories = db.relationship(CategoryModel, secondary='torrent.torrent_category')
    files = db.relationship(TorrentFileModel)

    def __init__(self, id, info_hash, name, url, description, info, uploaded_time, download_count, downloaded, seeders,
                 leechers, last_checked, user_create):
        self.id = id
        self.info_hash = info_hash
        self.name = name
        self.url = url
        self.description = description
        self.info = info
        self.uploaded_time = uploaded_time
        self.download_count = download_count
        self.downloaded = downloaded
        self.seeders = seeders
        self.leechers = leechers
        self.last_checked = last_checked
        self.user_create = user_create

    def json(self, jsondepth=0):
        json = {
            'id': self.id,
            'info_hash': self.info_hash,
            'name': self.name,
            'url': self.url,
            'description': self.description,
            'info': self.info,
            'uploaded_time': self.uploaded_time,
            'download_count': self.download_count,
            'downloaded': self.downloaded,
            'seeders': self.seeders,
            'leechers': self.leechers,
            'last_checked': self.last_checked,
            'user_create': self.user_create,
        }
        if jsondepth > 0:
            if self.categories:
                json['categories'] = [x.json(jsondepth) for x in self.categories]
                torrent_category = TorrentCategoryModel.query.filter_by(torrent_id=self.id, principal=True).first()
                if torrent_category:
                    for cat in json['categories']:
                        if cat['id'] == torrent_category.category_id:
                            cat['principal'] = True

            if self.files:
                json['cover'] = [x.json(jsondepth) for x in self.files if x.principal and x.module != 'TORRENT'].pop()
                json['images'] = [x.json(jsondepth) for x in self.files if not x.principal and x.module != 'TORRENT']

        return json

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
        for no_pk_key in ['info_hash', 'name', 'url', 'description', 'info', 'uploaded_time', 'download_count',
                          'downloaded', 'seeders', 'leechers', 'last_checked', 'user_create']:
            _assign_if_something(self, newdata, no_pk_key)
