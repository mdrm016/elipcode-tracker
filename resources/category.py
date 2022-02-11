import logging

from flasgger import swag_from
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse
from models.category import CategoryModel
from utils import restrict, check, paginated_results


class Category(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int)
    parser.add_argument('image_path', type=str)
    parser.add_argument('name', type=str)

    @jwt_required
    @check('categories_get')
    @swag_from('../swagger/categories/get_categories.yaml')
    def get(self, id):
        category = CategoryModel.find_by_id(id)
        if category:
            return category.json()
        return {'message': 'No se encuentra Categories'}, 404

    @jwt_required
    @check('categories_update')
    @swag_from('../swagger/categories/put_categories.yaml')
    def put(self, id):
        category = CategoryModel.find_by_id(id)
        if category:
            newdata = Category.parser.parse_args()
            category.from_reqparse(newdata)
            category.save_to_db()
            return category.json()
        return {'message': 'No se encuentra Categories'}, 404

    @jwt_required
    @check('categories_delete')
    @swag_from('../swagger/categories/delete_categories.yaml')
    def delete(self, id):
        category = CategoryModel.find_by_id(id)
        if category:
            category.delete_from_db()

        return {'message': 'Se ha borrado Categories'}


class CategoryList(Resource):

    @jwt_required
    @check('categories_list')
    @swag_from('../swagger/categories/list_categories.yaml')
    def get(self):
        query = CategoryModel.query
        return paginated_results(query)

    @jwt_required
    @check('categories_insert')
    @swag_from('../swagger/categories/post_categories.yaml')
    def post(self):
        data = Category.parser.parse_args()

        id = data.get('id')

        if id is not None and CategoryModel.find_by_id(id):
            return {'message': "Ya existe un categories con id '{}'.".format(id)}, 400

        category = CategoryModel(**data)
        try:
            category.save_to_db()
        except Exception as e:
            logging.error('Ocurrió un error al crear Cliente.', exc_info=e)
            return {"message": "Ocurrió un error al crear Categories."}, 500

        return category.json(), 201


class CategorySearch(Resource):

    @jwt_required
    @check('categories_search')
    @swag_from('../swagger/categories/search_categories.yaml')
    def post(self):
        query = CategoryModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'id', lambda x: CategoryModel.id == x)
            query = restrict(query, filters, 'image_path', lambda x: CategoryModel.image_path.contains(x))
            query = restrict(query, filters, 'name', lambda x: CategoryModel.name.contains(x))
        return paginated_results(query)
