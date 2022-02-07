import base64
import logging
from datetime import datetime

from flasgger import swag_from
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse
from models.categories import CategoriesModel
from utils import restrict, check, paginated_results


class Categories(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int)
    parser.add_argument('image', type=str)
    parser.add_argument('name', type=str)

    @jwt_required
    @check('categories_get')
    @swag_from('../swagger/categories/get_categories.yaml')
    def get(self, id):
        categories = CategoriesModel.find_by_id(id)
        if categories:
            return categories.json()
        return {'message': 'No se encuentra Categories'}, 404

    @jwt_required
    @check('categories_update')
    @swag_from('../swagger/categories/put_categories.yaml')
    def put(self, id):
        categories = CategoriesModel.find_by_id(id)
        if categories:
            newdata = Categories.parser.parse_args()
            categories.from_reqparse(newdata)
            categories.save_to_db()
            return categories.json()
        return {'message': 'No se encuentra Categories'}, 404

    @jwt_required
    @check('categories_delete')
    @swag_from('../swagger/categories/delete_categories.yaml')
    def delete(self, id):
        categories = CategoriesModel.find_by_id(id)
        if categories:
            categories.delete_from_db()

        return {'message': 'Se ha borrado Categories'}


class CategoriesList(Resource):

    @jwt_required
    @check('categories_list')
    @swag_from('../swagger/categories/list_categories.yaml')
    def get(self):
        query = CategoriesModel.query
        return paginated_results(query)

    @jwt_required
    @check('categories_insert')
    @swag_from('../swagger/categories/post_categories.yaml')
    def post(self):
        data = Categories.parser.parse_args()

        id = data.get('id')

        if id is not None and CategoriesModel.find_by_id(id):
            return {'message': "Ya existe un categories con id '{}'.".format(id)}, 400

        categories = CategoriesModel(**data)
        try:
            categories.save_to_db()
        except Exception as e:
            logging.error('Ocurrió un error al crear Cliente.', exc_info=e)
            return {"message": "Ocurrió un error al crear Categories."}, 500

        return categories.json(), 201


class CategoriesSearch(Resource):

    @jwt_required
    @check('categories_search')
    @swag_from('../swagger/categories/search_categories.yaml')
    def post(self):
        query = CategoriesModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'id', lambda x: CategoriesModel.id == x)
            query = restrict(query, filters, 'image', lambda x: CategoriesModel.image.contains(x))
            query = restrict(query, filters, 'name', lambda x: CategoriesModel.name.contains(x))
        return paginated_results(query)
