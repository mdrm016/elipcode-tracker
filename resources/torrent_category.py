import base64
import logging
from datetime import datetime

from flasgger import swag_from
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse
from models.torrent_category import TorrentCategoryModel
from utils import restrict, check, paginated_results


class TorrentCategory(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int)
    parser.add_argument('torrent_id', type=int)
    parser.add_argument('category_id', type=int)

    @jwt_required
    @check('torrent_category_get')
    @swag_from('../swagger/torrent_category/get_torrent_category.yaml')
    def get(self, id):
        torrent_category = TorrentCategoryModel.find_by_id(id)
        if torrent_category:
            return torrent_category.json()
        return {'message': 'No se encuentra Torrent Category'}, 404

    @jwt_required
    @check('torrent_category_update')
    @swag_from('../swagger/torrent_category/put_torrent_category.yaml')
    def put(self, id):
        torrent_category = TorrentCategoryModel.find_by_id(id)
        if torrent_category:
            newdata = TorrentCategory.parser.parse_args()
            torrent_category.from_reqparse(newdata)
            torrent_category.save_to_db()
            return torrent_category.json()
        return {'message': 'No se encuentra Torrent Category'}, 404

    @jwt_required
    @check('torrent_category_delete')
    @swag_from('../swagger/torrent_category/delete_torrent_category.yaml')
    def delete(self, id):
        torrent_category = TorrentCategoryModel.find_by_id(id)
        if torrent_category:
            torrent_category.delete_from_db()

        return {'message': 'Se ha borrado Torrent Category'}


class TorrentCategoryList(Resource):

    @jwt_required
    @check('torrent_category_list')
    @swag_from('../swagger/torrent_category/list_torrent_category.yaml')
    def get(self):
        query = TorrentCategoryModel.query
        return paginated_results(query)

    @jwt_required
    @check('torrent_category_insert')
    @swag_from('../swagger/torrent_category/post_torrent_category.yaml')
    def post(self):
        data = TorrentCategory.parser.parse_args()

        id = data.get('id')

        if id is not None and TorrentCategoryModel.find_by_id(id):
            return {'message': "Ya existe un torrent_category con id '{}'.".format(id)}, 400

        torrent_category = TorrentCategoryModel(**data)
        try:
            torrent_category.save_to_db()
        except Exception as e:
            logging.error('Ocurrió un error al crear Cliente.', exc_info=e)
            return {"message": "Ocurrió un error al crear Torrent Category."}, 500

        return torrent_category.json(), 201


class TorrentCategorySearch(Resource):

    @jwt_required
    @check('torrent_category_search')
    @swag_from('../swagger/torrent_category/search_torrent_category.yaml')
    def post(self):
        query = TorrentCategoryModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'id', lambda x: TorrentCategoryModel.id == x)
            query = restrict(query, filters, 'torrent_id', lambda x: TorrentCategoryModel.torrent_id == x)
            query = restrict(query, filters, 'category_id', lambda x: TorrentCategoryModel.category_id == x)
        return paginated_results(query)
