import base64

from flask_restful.reqparse import Namespace

from db import db
from models.torrents import TorrentsModel
from models.users import UsersModel
from utils import _assign_if_something


class PeersModel(db.Model):
    __tablename__ = 'peers'

    id = db.Column(db.Integer, primary_key=True)
    peer_id = db.Column(db.String)
    torrent_id = db.Column(db.Integer, db.ForeignKey('torrents.torrent_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    ip = db.Column(db.String)
    port = db.Column(db.Integer)
    active = db.Column(db.Boolean)
    uploaded = db.Column(db.Integer, default=0)
    downloaded = db.Column(db.Integer, default=0)
    uploaded_total = db.Column(db.Integer, default=0)
    downloaded_total = db.Column(db.Integer, default=0)
    seeding = db.Column(db.Boolean, default=False)

    torrent = db.relationship(TorrentsModel, backref='peers')
    user = db.relationship(UsersModel, backref='activity')

    def __init__(self, id, peer_id, torrent_id, user_id, ip, port, active, uploaded, downloaded, uploaded_total, downloaded_total, seeding):
        self.id = id
        self.peer_id = peer_id
        self.torrent_id = torrent_id
        self.user_id = user_id
        self.ip = ip
        self.port = port
        self.active = active
        self.uploaded = uploaded
        self.downloaded = downloaded
        self.uploaded_total = uploaded_total
        self.downloaded_total = downloaded_total
        self.seeding = seeding

    def json(self, jsondepth=0):
        return {
            'id': self.id,
            'peer_id': self.peer_id,
            'torrent_id': self.torrent_id,
            'user_id': self.user_id,
            'ip': self.ip,
            'port': self.port,
            'active': self.active,
            'uploaded': self.uploaded,
            'downloaded': self.downloaded,
            'uploaded_total': self.uploaded_total,
            'downloaded_total': self.downloaded_total,
            'seeding': self.seeding,
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
        for no_pk_key in ['peer_id','torrent_id','user_id','ip','port','active','uploaded','downloaded','uploaded_total','downloaded_total','seeding']:
            _assign_if_something(self, newdata, no_pk_key)

