from flask_restful.reqparse import Namespace

from db import db
from utils import _assign_if_something


class TorrentFileModel(db.Model):
    __tablename__ = 'torrent_file'
    __table_args__ = {"schema": "torrent"}

    id = db.Column(db.BigInteger, primary_key=True)
    torrent_id = db.Column(db.BigInteger, db.ForeignKey('torrent.torrent.id'))
    module = db.Column(db.String(15))
    principal = db.Column(db.Boolean, nullable=False, default=False)
    file_name = db.Column(db.String)
    mime_type = db.Column(db.String(100))
    path = db.Column(db.String(300))
    user_create = db.Column(db.String(30))
    date_create = db.Column(db.DateTime)

    def __init__(self, module, principal, file_name, mime_type, path, user_create, date_create):
        # self.torrent_id = torrent_id
        self.module = module
        self.principal = principal
        self.file_name = file_name
        self.mime_type = mime_type
        self.path = path
        self.user_create = user_create
        self.date_create = date_create

    def json(self, jsondepth=0):
        return {
            'id': self.id,
            'torrent_id': self.torrent_id,
            'module': self.module,
            'principal': self.principal,
            'file_name': self.file_name,
            'mime_type': self.mime_type,
            'path': self.path,
            'user_create': self.user_create,
            'date_create': self.date_create,
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
        for no_pk_key in ['torrent_id', 'module', 'principal', 'file_name', 'mime_type', 'path', 'user_create', 'date_create']:
            _assign_if_something(self, newdata, no_pk_key)
