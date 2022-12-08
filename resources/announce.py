import datetime
import sys
from ipaddress import ip_address

import bencode
import ipaddr
from flask import request, Response, current_app, make_response
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource, reqparse

from sqlalchemy.sql.expression import func

from models.peers import PeersModel
from models.torrent import TorrentModel
from models.user import UserModel

import struct
import logging

from utils import check, tracker_error, parse_request

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

    def get(self, passkey):

        # Parse the request and return any errors
        values, response = parse_request(request)
        if response is not None:
            return tracker_error(response)

        # Authenticate the user
        user = UserModel.query.filter_by(passkey=passkey).first()
        if not user:
            print("Invalid passkey", file=sys.stdout)
            return failure('Invalid passkey')

        # Authenticate the info_hash
        torrent = TorrentModel.query.filter_by(info_hash=values['info_hash']).first()
        if not torrent:
            print("Torrent not found or no registered", file=sys.stdout)
            return failure("Torrent not found or no registered")

        # Se obtiene el peer que realiza la peticion
        peer = PeersModel.query.filter_by(peer_id=values['peer_id']).first()
        left = values['left']
        if not peer:
            peer = PeersModel()
            peer.user = user
            peer.torrent = torrent
            peer.peer_id = values['peer_id']
            peer.uploaded = 0
            peer.downloaded = 0
            peer.uploaded_total = 0
            peer.downloaded_total = 0
            peer.seeding = False

        # Se inicializa los cambios de la peticion
        diff_uploaded = 0
        if values['uploaded']:
            diff_uploaded = values['uploaded'] - peer.uploaded
        diff_downloaded = 0
        if values['downloaded']:
            diff_downloaded = values['downloaded'] - peer.downloaded
        compactmode = False
        if values['compact'] == 1:
            compactmode = True
        peer.ip = values['ip']
        peer.port = values['port']

        # Se evalua si el peer es seeder o leecher
        if left == 0:
            peer.seeding = True
            torrent.save_to_db()
        else:
            peer.seeding = False

        # Dependiendo del evento se realiza cambios al usuario, torrent y peer
        if 'event' in values:
            event = values['event']
            if event == 'started':
                peer.active = True
                peer.uploaded = values['uploaded']
                peer.downloaded = values['downloaded']
                peer.uploaded_total += values['uploaded']
                peer.downloaded_total += values['downloaded']
                user.uploaded += values['uploaded']
                user.downloaded += values['downloaded']
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
                peer.uploaded = values['uploaded']
                peer.downloaded = values['downloaded']
                peer.uploaded_total += diff_uploaded
                peer.downloaded_total += diff_downloaded
                user.uploaded += diff_uploaded
                user.downloaded += diff_downloaded
        else:
            peer.uploaded = values['uploaded']
            peer.downloaded = values['downloaded']
            peer.uploaded_total += diff_uploaded
            peer.downloaded_total += diff_downloaded
            user.uploaded += diff_uploaded
            user.downloaded += diff_downloaded

        # Se habilita seeder despues de 20 segundos y se actualiza los valores del torrent
        if torrent.last_checked is None or (datetime.datetime.now() - torrent.last_checked).seconds >= 20:
            seeders = 0
            leechers = 0
            for i in torrent.peers:
                if i.active:
                    if i.seeding:
                        seeders += 1
                    else:
                        leechers += 1
            torrent.seeders = seeders
            torrent.leechers = leechers
            torrent.last_checked = datetime.datetime.now()
            torrent.save_to_db()

        # Al guardar el peer con los valores relacionados al modelo
        peer.save_to_db()

        if compactmode:
            if peer.seeding:
                print(f"Peer is seed: {peer.peer_id}", file=sys.stdout)
                # Si el peer esta sembrando, se le pasa hasta 50 sangijuelas
                peer_objs = PeersModel.query.filter_by(torrent=torrent).filter_by(active=True).filter_by(
                    seeding=False).order_by(func.random()).limit(50).all()
            else:
                print(f"Peer is leecher: {peer.peer_id}", file=sys.stdout)
                # Si el peer esta requiriendo el torrent, se le pasa hasta 50 sembradores y hasta 50 sangijuejas
                peer_objs = PeersModel.query.filter_by(torrent=torrent).filter_by(active=True).filter_by(
                    seeding=True).order_by(func.random()).limit(25).all()
                peer_objs += PeersModel.query.filter_by(torrent=torrent).filter_by(active=True).filter_by(
                    seeding=False).order_by(func.random()).limit(25).all()

            # Se envia la cantidad de peers solicitada por el cliente
            peer_objs = peer_objs[:values['numwant']]

            # Se prepara concatenacion de peers en COMPACT MODE
            print("COMPACT MODE", file=sys.stdout)
            peers = b""
            for i in peer_objs:
                if i != peer:   # No enviar el peer que realiza la peticion
                    print(f'Peer to response --> {i.ip}:{i.port}', file=sys.stdout)
                    ipsplit = i.ip.split(".")
                    peers += struct.pack(">BBBBH", int(ipsplit[0]), int(ipsplit[1]), int(ipsplit[2]), int(ipsplit[3]), i.port)
            # peers += struct.pack(">BBBBH", 54, 233, 192, 213, 6948)
            peers += struct.pack(">BBBBH", 181, 78, 27, 190, 46269)

            # Alternativa
            # peers2 = b"".join(ip_address(p.ip).packed + p.port.to_bytes(2, "big") for p in peer_objs)
            print('ALTERNATIVA', file=sys.stdout)
            peers2 = b""
            for p in peer_objs:
                if p != peer:
                    print(f'Peer to response --> {p.ip}:{p.port}', file=sys.stdout)
                    print('ip', ip_address(p.ip).packed, file=sys.stdout)
                    print('port', p.port.to_bytes(2, "big"), file=sys.stdout)
                    peers2 += ip_address(p.ip).packed + p.port.to_bytes(2, "big")

            print("peers codification", peers, peers2, file=sys.stdout)

            # Se prepara objeto a responder
            data = {
                'interval': 60,  # get_interval(peer),
                'tracker id': current_app.config['TRACKER_ID'],
                'complete': torrent.seeders,
                'incomplete': torrent.leechers,
                'peers': peers
            }

            print(f"Data to response: {data}", file=sys.stdout)
            response = make_response(bencode.bencode(data), 200)
            response.mimetype = "text/plain"
            return response

        if values['no_peer_id'] == 0:
            if peer.seeding:
                print(f"Peer is seed: {peer.peer_id}", file=sys.stdout)
                peer_objs = PeersModel.query.filter_by(active=True).filter_by(torrent=torrent).filter_by(
                    seeding=False).order_by(func.random()).limit(50).all()
            else:
                print(f"Peer is leecher: {peer.peer_id}", file=sys.stdout)
                peer_objs = PeersModel.query.filter_by(active=True).filter_by(torrent=torrent).filter_by(
                    seeding=True).order_by(func.random()).limit(25).all()
                peer_objs += PeersModel.query.filter_by(active=True).filter_by(torrent=torrent).filter_by(
                    seeding=False).order_by(func.random()).limit(25).all()

            # Se envia la cantidad de peers solicitada por el cliente
            peer_objs = peer_objs[:values['numwant']]

            print("NOT COMPACT MODE", file=sys.stdout)
            log.info("NOT COMPACT MODE")
            peers = list()
            for i in peer_objs:
                if i != peer:   # No enviar el peer que realiza la peticion
                    print(f'Peer to response --> {i.ip}:{i.port}', file=sys.stdout)
                    peers.append({'peer id': i.peer_id, 'ip': i.ip, 'port': i.port})

            # Se prepara objeto a responder
            data = {
                'interval': 60,  # get_interval(peer),
                'tracker id': current_app.config['TRACKER_ID'],
                'complete': torrent.seeders,
                'incomplete': torrent.leechers,
                'peers': peers
            }

            print(data, file=sys.stdout)
            response = make_response(bencode.bencode(data), 200)
            response.mimetype = "text/plain"
            return response
        else:
            print("NO_PEER_ID", file=sys.stdout)
            log.error("NO_PEER_ID")
