import base64
import hashlib
import logging
import os
import shutil
from datetime import datetime

import bencodepy
from flasgger import swag_from
from flask import request, current_app, send_file
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse
from pytz import unicode
from werkzeug.utils import secure_filename

from file_utils import get_filename_hash, get_file_directory
from models.torrents import TorrentsModel
from utils import restrict, check, paginated_results

log = logging.getLogger(__name__)


class Torrents(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('torrent_id', type=int)
    parser.add_argument('info_hash', type=str)
    parser.add_argument('name', type=str)
    parser.add_argument('description', type=str)
    parser.add_argument('info', type=lambda x: base64.decodebytes(x.encode()))
    parser.add_argument('torrent_file', type=str)
    parser.add_argument('uploaded_time', type=lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'))
    parser.add_argument('download_count', type=int)
    parser.add_argument('seeders', type=int)
    parser.add_argument('leechers', type=int)
    parser.add_argument('last_checked', type=lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'))
    parser.add_argument('category_id', type=int)

    @jwt_required
    @check('torrents_get')
    @swag_from('../swagger/torrents/get_torrents.yaml')
    def get(self, id):
        torrents = TorrentsModel.find_by_id(id)
        if torrents:
            return torrents.json()
        return {'message': 'No se encuentra Torrents'}, 404

    @jwt_required
    @check('torrents_update')
    @swag_from('../swagger/torrents/put_torrents.yaml')
    def put(self, id):
        torrents = TorrentsModel.find_by_id(id)
        if torrents:
            newdata = Torrents.parser.parse_args()
            torrents.from_reqparse(newdata)
            torrents.save_to_db()
            return torrents.json()
        return {'message': 'No se encuentra Torrents'}, 404

    @jwt_required
    @check('torrents_delete')
    @swag_from('../swagger/torrents/delete_torrents.yaml')
    def delete(self, id):
        torrents = TorrentsModel.find_by_id(id)
        if torrents:
            torrents.delete_from_db()

        return {'message': 'Se ha borrado Torrents'}


def save_torrent(torrent_file):
    if not getattr(torrent_file, 'filename', None):
        return None

    # ext = os.path.splitext(torrent_file.filename)[1]
    # d = [random.choice(string.ascii_letters) for x in xrange(16)]
    # filename = "".join(d)+ext
    # abs_filename = os.path.join(request.registry.settings['torrent_dir'], filename)

    filename_clean = secure_filename(get_filename_hash(torrent_file.filename))
    filename = "{}{}".format(current_app.config['TORRENT_FILES_PREFIX'], filename_clean)
    file_path_destination = os.path.join(get_file_directory(current_app.config['TORRENT_FILES_MODULE']), filename)

    perm_file = open(file_path_destination, 'wb')
    shutil.copyfileobj(torrent_file, perm_file)
    torrent_file.close()
    perm_file.close()
    return file_path_destination


class TorrentsList(Resource):

    @jwt_required
    @check('torrents_list')
    @swag_from('../swagger/torrents/list_torrents.yaml')
    def get(self):
        query = TorrentsModel.query
        return paginated_results(query)

    @jwt_required
    @check('torrents_insert')
    @swag_from('../swagger/torrents/post_torrents.yaml')
    def post(self):
        data = Torrents.parser.parse_args()

        torrent_id = data.get('torrent_id')
        if torrent_id is not None and TorrentsModel.find_by_torrent_id(torrent_id):
            return {'message': "Ya existe un torrents con id '{}'.".format(torrent_id)}, 400

        # Check if the torrent file was send via post request how file part
        if 'torrent_file' not in request.files:
            return {'error': "Torrent file no was send."}, 400
        torrent_file = request.files['torrent_file']

        torrent_path = save_torrent(torrent_file)
        if torrent_path is None:
            return {'error': "Torrent file could not be obtained."}, 400

        info = bencodepy.bencode(bencodepy.bdecode(open(torrent_path, 'rb').read())[b'info'])
        info_hash = hashlib.sha1(info).hexdigest()
        log.info('INFOHASH: %s', info_hash)

        torrent = TorrentsModel(**data)
        torrent.info_hash = info_hash
        torrent.torrent_file = torrent_path
        torrent.name = unicode(torrent.name)
        torrent.info = {}
        torrent.uploaded_time = datetime.now()
        torrent.last_checked = datetime.now()

        # TODO: definir la categoría del torrent

        try:
            torrent.save_to_db()
        except Exception as e:
            logging.error('Ocurrió un error al crear el Torrent.', exc_info=e)
            return {"error": "Ocurrió un error al crear Torrents."}, 500

        return {"msg": "Torrent file created."}, 201


class TorrentsSearch(Resource):

    @jwt_required
    @check('torrents_search')
    @swag_from('../swagger/torrents/search_torrents.yaml')
    def post(self):
        query = TorrentsModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'torrent_id', lambda x: TorrentsModel.torrent_id == x)
            query = restrict(query, filters, 'info_hash', lambda x: TorrentsModel.info_hash.contains(x))
            query = restrict(query, filters, 'name', lambda x: TorrentsModel.name.contains(x))
            query = restrict(query, filters, 'desc', lambda x: TorrentsModel.desc.contains(x))
            query = restrict(query, filters, 'torrent_file', lambda x: TorrentsModel.torrent_file.contains(x))
            query = restrict(query, filters, 'download_count', lambda x: TorrentsModel.download_count == x)
            query = restrict(query, filters, 'seeders', lambda x: TorrentsModel.seeders == x)
            query = restrict(query, filters, 'leechers', lambda x: TorrentsModel.leechers == x)
            query = restrict(query, filters, 'category_id', lambda x: TorrentsModel.category_id == x)
        return paginated_results(query)


class TorrentFiles(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('torrent_id', type=int)

    def get(self, torrent_id):
        torrent = TorrentsModel.find_by_torrent_id(torrent_id)

        if not torrent:
            return {"error": "Torrent not found"}, 404

        return send_file(torrent.torrent_file, as_attachment=True)
