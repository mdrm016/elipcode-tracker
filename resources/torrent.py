import base64
import hashlib
import logging
from datetime import datetime

import bencodepy
from flasgger import swag_from
from flask import request, json, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, reqparse
from pytz import unicode

from file_utils import save_file, cheksum_file, delete_files_by_hash_datetime
from models.category import CategoryModel
from models.torrent import TorrentModel
from models.torrent_category import TorrentCategoryModel
from models.torrent_file import TorrentFileModel
from torrent_utils import get_torrent_info
from utils import restrict, check, paginated_results

log = logging.getLogger(__name__)


class Torrents(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int)
    parser.add_argument('info_hash', type=str)
    parser.add_argument('name', type=str)
    parser.add_argument('url', type=str)
    parser.add_argument('description', type=str)
    parser.add_argument('info', type=lambda x: base64.decodebytes(x.encode()))
    parser.add_argument('uploaded_time', type=lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'))
    parser.add_argument('download_count', type=int)
    parser.add_argument('downloaded', type=int)
    parser.add_argument('seeders', type=int)
    parser.add_argument('leechers', type=int)
    parser.add_argument('last_checked', type=lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'))
    parser.add_argument('user_create', type=str)

    @jwt_required
    @check('torrents_get')
    @swag_from('../swagger/torrents/get_torrents.yaml')
    def get(self, id):
        torrent = TorrentModel.find_by_torrent_id(id)
        # if not torrent.info:
        #     torrent_file = [x for x in torrent.files if x.module == 'TORRENT'].pop()
        #     torrent.info = get_torrent_info(torrent_file.path)
        #     torrent.save_to_db()
        if torrent:
            return torrent.json(jsondepth=1)
        return {'message': 'Torrent not found'}, 404

    @jwt_required
    @check('torrents_update')
    @swag_from('../swagger/torrents/put_torrents.yaml')
    def put(self, id):
        torrent = TorrentModel.find_by_torrent_id(id)
        if torrent:
            newdata = Torrents.parser.parse_args()
            torrent.from_reqparse(newdata)
            torrent.save_to_db()
            return torrent.json()
        return {'message': 'No se encuentra Torrent'}, 404

    @jwt_required
    @check('torrents_delete')
    @swag_from('../swagger/torrents/delete_torrents.yaml')
    def delete(self, id):
        torrent = TorrentModel.find_by_torrent_id(id)
        if torrent:
            torrent.delete_from_db()

        return {'message': 'Se ha borrado Torrent'}


class TorrentsList(Resource):

    @jwt_required
    @check('torrents_list')
    @swag_from('../swagger/torrents/list_torrents.yaml')
    def get(self):
        query = TorrentModel.query
        return paginated_results(query)

    @jwt_required
    @check('torrents_insert')
    @swag_from('../swagger/torrents/post_torrents.yaml')
    def post(self):
        data = Torrents.parser.parse_args()

        torrent = TorrentModel(**data)
        torrent.name = unicode(torrent.name)
        torrent.uploaded_time = datetime.now()
        torrent.last_checked = datetime.now()
        torrent.user_create = get_jwt_identity()

        # Chech if exist almost one category
        categories = json.loads(request.values['categories'])
        if not categories:
            return {'error': "Torrent does not have a category."}, 400

        # Check if the torrent file was send via post request how file part
        if 'torrent_file' not in request.files:
            return {'error': "Torrent file no was send."}, 400
        torrent_file_request = request.files['torrent_file']

        # Generate hash by torrent file
        torrent_file_cheksum = cheksum_file(torrent_file_request)
        if not torrent_file_cheksum:
            return {'error': "Torrent file cheksum not generate."}, 500

        # Save the torrent file
        torrent_file = save_file(file=torrent_file_request, principal=True, hash=torrent_file_cheksum,
                                 date_time=torrent.uploaded_time)  # Return model TorrentFile
        if torrent_file is None:
            return {'error': "Torrent file could not be obtained."}, 400
        torrent.files.append(torrent_file)

        # Get Torrent Info Hash
        info = bencodepy.bencode(bencodepy.bdecode(open(torrent_file.path, 'rb').read())[b'info'])
        info_hash = hashlib.sha1(info).hexdigest()
        torrent.info_hash = info_hash
        logging.info('INFOHASH: %s', info_hash)

        # Save torrent info
        torrent.info = get_torrent_info(torrent_file.path)

        # Get torrent images
        torrent_images_request = request.files.getlist('torrent_images[]')
        if not torrent_images_request:
            return {'error': "Torrent does not have a image."}, 400
        for idx, torrent_image_request in enumerate(torrent_images_request):
            torrent_image = save_file(file=torrent_image_request, hash=torrent_file_cheksum,
                                      date_time=torrent.uploaded_time)
            if torrent_image:
                if idx == 0:
                    torrent_image.principal = True  # First Image is principal
                torrent.files.append(torrent_image)

        # Add categories
        for category in categories:
            categoryModel = CategoryModel.query.filter_by(name=category['name']).first()
            torrent.categories.append(categoryModel)

        try:
            torrent.save_to_db()

            # First category is principal
            principalCategory = CategoryModel.query.filter_by(name=torrent.categories[0].name).first()
            torrent_category = TorrentCategoryModel.query.filter_by(torrent_id=torrent.id,
                                                                    category_id=principalCategory.id).first()
            torrent_category.principal = True
            torrent_category.save_to_db()

        except Exception as error:
            logging.error('An error occurred while creating the Torrent.', exc_info=error)
            # Delete all files by torrent checksum
            delete_files_by_hash_datetime(torrent_file_cheksum, torrent.uploaded_time)
            return {"error": "An error occurred while creating the Torrent."}, 500

        return {"msg": "Torrent file created."}, 201


class TorrentsSearch(Resource):

    @jwt_required
    @check('torrents_search')
    @swag_from('../swagger/torrents/search_torrents.yaml')
    def post(self):
        query = TorrentModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'id', lambda x: TorrentModel.id == x)
            query = restrict(query, filters, 'info_hash', lambda x: TorrentModel.info_hash.contains(x))
            query = restrict(query, filters, 'name', lambda x: TorrentModel.name.contains(x))
            query = restrict(query, filters, 'description', lambda x: TorrentModel.description.contains(x))
            query = restrict(query, filters, 'download_count', lambda x: TorrentModel.download_count == x)
            query = restrict(query, filters, 'seeders', lambda x: TorrentModel.seeders == x)
            query = restrict(query, filters, 'leechers', lambda x: TorrentModel.leechers == x)
            query = restrict(query, filters, 'user_create', lambda x: TorrentModel.user_create == x)

        # order section
        query = query.order_by(TorrentModel.uploaded_time.desc())

        return paginated_results(query)


class TorrentFiles(Resource):

    @jwt_required
    # @check('torrent_file_download')
    def get(self, id):
        torrent = TorrentModel.find_by_torrent_id(id)

        if not torrent:
            return {"error": "Torrent not found"}, 404

        torrent_file = next(x for x in torrent.files if x.module == 'TORRENT')
        new_filename = "{} - {}".format(current_app.config['TORRENT_FILES_PREFIX'], torrent_file.file_name)
        if torrent_file:
            response = send_file(torrent_file.path, attachment_filename=new_filename, as_attachment=True)
            response.headers["x-filename"] = new_filename
            response.headers["Access-Control-Expose-Headers"] = 'x-filename'
            return response

        return {'error': "Torrent not found."}, 404
