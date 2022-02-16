import base64
import logging
from datetime import datetime

from flasgger import swag_from
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse
from models.torrent_file import TorrentFileModel
from utils import restrict, check, paginated_results


class TorrentFile(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int)
    parser.add_argument('torrent_id', type=int)
    parser.add_argument('module', type=str)
    parser.add_argument('file_name', type=str)
    parser.add_argument('mime_type', type=str)
    parser.add_argument('path', type=str)
    parser.add_argument('user_create', type=str)
    parser.add_argument('date_create', type=lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'))

    @jwt_required
    @check('torrent_file_get')
    @swag_from('../swagger/torrent_file/get_torrent_file.yaml')
    def get(self, id):
        torrent_file = TorrentFileModel.find_by_id(id)
        if torrent_file:
            return torrent_file.json()
        return {'message': 'No se encuentra Torrent File'}, 404

    @jwt_required
    @check('torrent_file_update')
    @swag_from('../swagger/torrent_file/put_torrent_file.yaml')
    def put(self, id):
        torrent_file = TorrentFileModel.find_by_id(id)
        if torrent_file:
            newdata = TorrentFile.parser.parse_args()
            torrent_file.from_reqparse(newdata)
            torrent_file.save_to_db()
            return torrent_file.json()
        return {'message': 'No se encuentra Torrent File'}, 404

    @jwt_required
    @check('torrent_file_delete')
    @swag_from('../swagger/torrent_file/delete_torrent_file.yaml')
    def delete(self, id):
        torrent_file = TorrentFileModel.find_by_id(id)
        if torrent_file:
            torrent_file.delete_from_db()

        return {'message': 'Se ha borrado Torrent File'}


class TorrentFileList(Resource):

    @jwt_required
    @check('torrent_file_list')
    @swag_from('../swagger/torrent_file/list_torrent_file.yaml')
    def get(self):
        query = TorrentFileModel.query
        return paginated_results(query)

    @jwt_required
    @check('torrent_file_insert')
    @swag_from('../swagger/torrent_file/post_torrent_file.yaml')
    def post(self):
        data = TorrentFile.parser.parse_args()

        id = data.get('id')

        if id is not None and TorrentFileModel.find_by_id(id):
            return {'message': "Ya existe un torrent_file con id '{}'.".format(id)}, 400

        torrent_file = TorrentFileModel(**data)
        try:
            torrent_file.save_to_db()
        except Exception as e:
            logging.error('Ocurrió un error al crear Cliente.', exc_info=e)
            return {"message": "Ocurrió un error al crear Torrent File."}, 500

        return torrent_file.json(), 201


class TorrentFileSearch(Resource):

    @jwt_required
    @check('torrent_file_search')
    @swag_from('../swagger/torrent_file/search_torrent_file.yaml')
    def post(self):
        query = TorrentFileModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'id', lambda x: TorrentFileModel.id == x)
            query = restrict(query, filters, 'torrent_id', lambda x: TorrentFileModel.torrent_id == x)
            query = restrict(query, filters, 'module', lambda x: TorrentFileModel.module.contains(x))
            query = restrict(query, filters, 'file_name', lambda x: TorrentFileModel.file_name.contains(x))
            query = restrict(query, filters, 'mime_type', lambda x: TorrentFileModel.mime_type.contains(x))
            query = restrict(query, filters, 'path', lambda x: TorrentFileModel.path.contains(x))
            query = restrict(query, filters, 'user_create', lambda x: TorrentFileModel.user_create.contains(x))
        return paginated_results(query)
