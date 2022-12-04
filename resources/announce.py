import cgi
import datetime
from binascii import b2a_hex
from urllib import parse
from urllib.parse import urlparse, parse_qsl

from flask import request, Response, current_app
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource, reqparse

from bencode import bencode
from sqlalchemy.sql.expression import func

from models.peers import PeersModel
from models.torrent import TorrentModel
from models.user import UserModel

import struct
import logging

from utils import check

log = logging.getLogger(__name__)


def failure(reason):
    return Response(bencode({'failure reason': reason}))


def get_announce():
    username = get_jwt_identity()
    user = UserModel.query.filter_by(username=username).first()
    if user is None:
        return None

    announce_url = "{}/{}/{}".format(current_app.config['ANNOUNCE_DOMAIN'], user.passkey, 'announce')
    return announce_url


class AnnounceMetadata(Resource):

    @jwt_required
    @check('announce_get')
    def get(self):
        announce_url = get_announce()
        if announce_url is None:
            log.error("User not found")
            return {"error": "User not found"}, 404

        return {"announce": announce_url}, 200


class Announce(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('passkey', type=str)

    def toHex(self, x):
        arr = []
        for c in x:
            try:
                coded = c.encode('latin_1')
                a = ord(c)
                b = hex(a)
                d = b[2:]
                e = d.zfill(2)
            except UnicodeEncodeError:
                byteString = c.encode('utf-8')
                e = ''.join('{:02x}'.format(x) for x in byteString)
            arr.append(e)
            # if prt:
            #     print(f'{c} -> {e}')
        return "".join(arr)

    def get(self, passkey):

        user = UserModel.query.filter_by(passkey=passkey).first()
        if not user:
            print("Invalid passkey")
            return failure('Invalid passkey')
        # toHex = lambda x: "".join([hex(ord(c))[2:].zfill(2) for c in x])
        # toHex = lambda x: "".join(["{:02X}".format(ord(c)) for c in x])
        parse_url = urlparse(request.url)
        query_dict = dict(parse_qsl(parse_url.query, encoding='latin_1'))

        infohash = self.toHex(query_dict['info_hash'])
        peer_id = self.toHex(query_dict['peer_id'])
        torrent = TorrentModel.query.filter_by(info_hash=infohash).first()

        if not torrent:
            print("Torrent not found or no registered")
            return failure("Torrent not found or no registered")
        peer = PeersModel.query.filter_by(peer_id=peer_id).first()
        left = int(query_dict['left'])
        if not peer:
            peer = PeersModel()
            peer.user = user
            peer.torrent = torrent
            peer.peer_id = peer_id
            peer.uploaded = 0
            peer.downloaded = 0
            peer.uploaded_total = 0
            peer.downloaded_total = 0
            peer.seeding = False

        diff_uploaded = 0
        if 'uploaded' in query_dict:
            diff_uploaded = int(query_dict['uploaded']) - peer.uploaded
        diff_downloaded = 0
        if 'downloaded' in query_dict:
            diff_downloaded = int(query_dict['downloaded']) - peer.downloaded
        compactmode = False
        if 'compact' in query_dict and query_dict['compact'] == '1':
            compactmode = True
        peer.ip = request.environ['REMOTE_ADDR']
        peer.port = int(query_dict['port'])

        if left == 0:
            peer.seeding = True
            torrent.save_to_db()
        else:
            peer.seeding = False

        if 'event' in query_dict:
            event = query_dict['event']
            if event == 'started':
                peer.active = True
                peer.uploaded = int(query_dict['uploaded'])
                peer.downloaded = int(query_dict['downloaded'])
                peer.uploaded_total += int(query_dict['uploaded'])
                peer.downloaded_total += int(query_dict['downloaded'])
                user.uploaded += int(query_dict['uploaded'])
                user.downloaded += int(query_dict['downloaded'])
            elif event == 'stopped':
                peer.active = False
                peer.uploaded = 0
                peer.downloaded = 0
                peer.uploaded_total += diff_uploaded
                peer.downloaded_total += diff_downloaded
                user.uploaded += diff_uploaded
                user.downloaded += diff_downloaded
            elif event == 'completed':
                peer.seeding = True
                torrent.download_count += 1
                peer.active = True
                peer.uploaded = int(query_dict['uploaded'])
                peer.downloaded = int(query_dict['downloaded'])
                peer.uploaded_total += diff_uploaded
                peer.downloaded_total += diff_downloaded
                user.uploaded += diff_uploaded
                user.downloaded += diff_downloaded
        else:
            peer.uploaded = int(query_dict['uploaded'])
            peer.downloaded = int(query_dict['downloaded'])
            peer.uploaded_total += diff_uploaded
            peer.downloaded_total += diff_downloaded
            user.uploaded += diff_uploaded
            user.downloaded += diff_downloaded

        if torrent.last_checked is None or (datetime.datetime.now() - torrent.last_checked).seconds >= 60 * 10:
            peer_objs = torrent.peers
            seeders = 0
            leechers = 0
            for i in peer_objs:
                if i.active:
                    if i.seeding:
                        seeders += 1
                    else:
                        leechers += 1
            torrent.seeders = seeders
            torrent.leechers = leechers
            torrent.last_checked = datetime.datetime.now()
            torrent.save_to_db()

        peer.save_to_db()  # al guardar el peer se guarda los cambios del usuario

        if compactmode:
            peers = b""
            if peer.seeding:
                print("peer is seeding")
                peer_objs = PeersModel.query.filter_by(torrent=torrent).filter_by(active=True).filter_by(
                    seeding=False).order_by(func.random()).limit(50).all()
            else:
                peer_objs = PeersModel.query.filter_by(torrent=torrent).filter_by(active=True).filter_by(
                    seeding=True).order_by(func.random()).limit(25).all() + \
                            PeersModel.query.filter_by(torrent=torrent).filter_by(active=True).filter_by(
                                seeding=False).order_by(func.random()).limit(25).all()
            for i in peer_objs:
                if i == peer:
                    continue

                print(i.ip)
                ipsplit = i.ip.split(".")
                peers += struct.pack(">BBBBH", int(ipsplit[0]), int(ipsplit[1]), int(ipsplit[2]), int(ipsplit[3]), i.port)
            # log.error(toHex(peers))
            print(self.toHex(peers.decode('latin_1')))
            data = {
                'interval': 60,
                'tracker id': 'BodyMuscle',
                'complete': torrent.seeders,
                'incomplete': torrent.leechers,
                'peers': peers
            }
            print(data)
            return Response(bencode(data))

        if not 'no_peer_id' in query_dict:
            log.info("NOT COMPACT MODE")
            peers = list()
            if peer.seeding:
                peer_objs = PeersModel.query.filter_by(active=True).filter_by(torrent=torrent).filter_by(
                    seeding=False).order_by(func.random()).limit(50).all()
            else:
                peer_objs = PeersModel.query.filter_by(active=True).filter_by(torrent=torrent).filter_by(
                    seeding=True).order_by(func.random()).limit(25).all() + PeersModel.query.filter_by(
                    active=True).filter_by(torrent=torrent).filter_by(seeding=False).order_by(func.random()).limit(
                    25).all()
            for i in peer_objs:
                if i == peer:
                    continue
                peers.append({'peer id': i.peer_id, 'ip': i.ip, 'port': i.port})
            # log.info(peers)
            data = {
                'interval': 1800,
                'tracker id': 'Hermes',
                'complete': torrent.seeders,
                'incomplete': torrent.leechers,
                'peers': peers
            }
            print(data)
            return Response(bencode(data))

        else:
            log.error("NO_PEER_ID")
