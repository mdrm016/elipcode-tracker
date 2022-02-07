import base64
import logging
from datetime import datetime

from flasgger import swag_from
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse
from models.peers import PeersModel
from utils import restrict, check, paginated_results


class Peers(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int)
    parser.add_argument('peer_id', type=str)
    parser.add_argument('torrent_id', type=int)
    parser.add_argument('user_id', type=int)
    parser.add_argument('ip', type=str)
    parser.add_argument('port', type=int)
    parser.add_argument('active', type=bool)
    parser.add_argument('uploaded', type=int)
    parser.add_argument('downloaded', type=int)
    parser.add_argument('uploaded_total', type=int)
    parser.add_argument('downloaded_total', type=int)
    parser.add_argument('seeding', type=bool)

    @jwt_required
    @check('peers_get')
    @swag_from('../swagger/peers/get_peers.yaml')
    def get(self, id):
        peers = PeersModel.find_by_id(id)
        if peers:
            return peers.json()
        return {'message': 'No se encuentra Peers'}, 404

    @jwt_required
    @check('peers_update')
    @swag_from('../swagger/peers/put_peers.yaml')
    def put(self, id):
        peers = PeersModel.find_by_id(id)
        if peers:
            newdata = Peers.parser.parse_args()
            peers.from_reqparse(newdata)
            peers.save_to_db()
            return peers.json()
        return {'message': 'No se encuentra Peers'}, 404

    @jwt_required
    @check('peers_delete')
    @swag_from('../swagger/peers/delete_peers.yaml')
    def delete(self, id):
        peers = PeersModel.find_by_id(id)
        if peers:
            peers.delete_from_db()

        return {'message': 'Se ha borrado Peers'}


class PeersList(Resource):

    @jwt_required
    @check('peers_list')
    @swag_from('../swagger/peers/list_peers.yaml')
    def get(self):
        query = PeersModel.query
        return paginated_results(query)

    @jwt_required
    @check('peers_insert')
    @swag_from('../swagger/peers/post_peers.yaml')
    def post(self):
        data = Peers.parser.parse_args()

        id = data.get('id')

        if id is not None and PeersModel.find_by_id(id):
            return {'message': "Ya existe un peers con id '{}'.".format(id)}, 400

        peers = PeersModel(**data)
        try:
            peers.save_to_db()
        except Exception as e:
            logging.error('Ocurrió un error al crear Cliente.', exc_info=e)
            return {"message": "Ocurrió un error al crear Peers."}, 500

        return peers.json(), 201


class PeersSearch(Resource):

    @jwt_required
    @check('peers_search')
    @swag_from('../swagger/peers/search_peers.yaml')
    def post(self):
        query = PeersModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'id', lambda x: PeersModel.id == x)
            query = restrict(query, filters, 'peer_id', lambda x: PeersModel.peer_id.contains(x))
            query = restrict(query, filters, 'torrent_id', lambda x: PeersModel.torrent_id == x)
            query = restrict(query, filters, 'user_id', lambda x: PeersModel.user_id == x)
            query = restrict(query, filters, 'ip', lambda x: PeersModel.ip.contains(x))
            query = restrict(query, filters, 'port', lambda x: PeersModel.port == x)
            query = restrict(query, filters, 'active', lambda x: x)
            query = restrict(query, filters, 'uploaded', lambda x: PeersModel.uploaded == x)
            query = restrict(query, filters, 'downloaded', lambda x: PeersModel.downloaded == x)
            query = restrict(query, filters, 'uploaded_total', lambda x: PeersModel.uploaded_total == x)
            query = restrict(query, filters, 'downloaded_total', lambda x: PeersModel.downloaded_total == x)
            query = restrict(query, filters, 'seeding', lambda x: x)
        return paginated_results(query)
