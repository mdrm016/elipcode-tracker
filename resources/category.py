import logging

from flasgger import swag_from
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse

from file_utils import save_system_file, delete_file
from models.category import CategoryModel
from utils import restrict, check, paginated_results


class Category(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('image_path', type=str)
    parser.add_argument('name', type=str)

    MODULE_FILES_NAME = 'category'

    @jwt_required
    @check('category_get')
    @swag_from('../swagger/categories/get_categories.yaml')
    def get(self, id):
        category = CategoryModel.find_by_id(id)
        if category:
            return category.json()
        return {'message': 'No se encuentra Categories'}, 404

    @jwt_required
    @check('category_update')
    @swag_from('../swagger/categories/put_categories.yaml')
    def put(self, id):
        category = CategoryModel.find_by_id(id)
        if not category:
            return {'message': 'No se encuentra Categories'}, 404

        newdata = Category.parser.parse_args()
        category.from_reqparse(newdata)

        # Si hay una nueva imagen
        if 'image' in request.files:
            category_image = request.files['image']
            if category_image:
                # Se borra la imagen anterior
                delete_file(category.image_path)
                # Se agrega la nueva imagen
                category.image_path = save_system_file(category_image, Category.MODULE_FILES_NAME)

        category.save_to_db()
        return {'msg': 'Category updated'}, 200


    @jwt_required
    @check('category_delete')
    @swag_from('../swagger/categories/delete_categories.yaml')
    def delete(self, id):
        category = CategoryModel.find_by_id(id)
        if category:
            try:
                category.delete_from_db()
            except Exception as e:
                return {'error': str(e.__cause__)}, 500

        return {'msg': 'Category deleted'}


class CategoryList(Resource):

    @jwt_required
    @check('category_list')
    @swag_from('../swagger/categories/list_categories.yaml')
    def get(self):
        query = CategoryModel.query
        return paginated_results(query)

    @jwt_required
    @check('category_insert')
    @swag_from('../swagger/categories/post_categories.yaml')
    def post(self):
        data = Category.parser.parse_args()

        category = CategoryModel.query.filter_by(name=data['name']).first()
        if category:
            return {"error": "This category already exist"}, 400

        if 'image' in request.files:
            category_image = request.files['image']
            if category_image:
                data['image_path'] = save_system_file(category_image, Category.MODULE_FILES_NAME)

        category = CategoryModel(**data)
        try:
            category.save_to_db()
        except Exception as e:
            return {"error": str(e.__cause__)}, 500

        return {"msg": "Category created"}, 201


class CategorySearch(Resource):

    @jwt_required
    @check('category_search')
    @swag_from('../swagger/categories/search_categories.yaml')
    def post(self):
        query = CategoryModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'id', lambda x: CategoryModel.id == x)
            query = restrict(query, filters, 'image_path', lambda x: CategoryModel.image_path.contains(x))
            query = restrict(query, filters, 'name', lambda x: CategoryModel.name.contains(x))
        return paginated_results(query)
