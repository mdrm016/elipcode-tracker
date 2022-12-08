import bencode
from flask import request, make_response
from flask_restful import Resource, reqparse

from models.torrent import TorrentModel


class Scrape(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('passkey', type=str)

    def get(self, passkey):
        args = request.args
        if not "info_hash" in args:
            txt = bencode.bencode({"failure reason": "Not enough query parameters provided"})
            response = make_response(txt, 400)
            response.mimetype = "text/plain"
            return response

        dct = {
            "files": {
            }
        }

        infoHashes = args.getlist("info_hash")
        for infoHash in infoHashes:
            torr = TorrentModel.query.filter_by(info_hash=infoHash).first()
            if torr is None:
                continue

            dct["files"][torr.infoHash] = {
                "complete": sum((1 if p.left == 0 else 0) for p in torr.peers),
                "downloaded": sum((1 if p.event == "completed" else 0) for p in torr.peers),
                "incomplete": sum((1 if p.left != 0 else 0) for p in torr.peers)
            }

        response = make_response(bencode.bencode(dct), 200)
        response.mimetype = "text/plain"
        return response
