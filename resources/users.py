import base64
import logging
from datetime import datetime

from flasgger import swag_from
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse
from models.users import UsersModel
from utils import restrict, check, paginated_results


class Users(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('user_id', type=int)
    parser.add_argument('username', type=str)
    parser.add_argument('password', type=str)
    parser.add_argument('passkey', type=str)
    parser.add_argument('uploaded', type=int)
    parser.add_argument('downloaded', type=int)
    parser.add_argument('email', type=str)

    @jwt_required
    @check('users_get')
    @swag_from('../swagger/users/get_users.yaml')
    def get(self, id):
        users = UsersModel.find_by_id(id)
        if users:
            return users.json()
        return {'message': 'No se encuentra Users'}, 404

    @jwt_required
    @check('users_update')
    @swag_from('../swagger/users/put_users.yaml')
    def put(self, id):
        users = UsersModel.find_by_id(id)
        if users:
            newdata = Users.parser.parse_args()
            users.from_reqparse(newdata)
            users.save_to_db()
            return users.json()
        return {'message': 'No se encuentra Users'}, 404

    @jwt_required
    @check('users_delete')
    @swag_from('../swagger/users/delete_users.yaml')
    def delete(self, id):
        users = UsersModel.find_by_id(id)
        if users:
            users.delete_from_db()

        return {'message': 'Se ha borrado Users'}


class UsersList(Resource):

    @jwt_required
    @check('users_list')
    @swag_from('../swagger/users/list_users.yaml')
    def get(self):
        query = UsersModel.query
        return paginated_results(query)

    @jwt_required
    @check('users_insert')
    @swag_from('../swagger/users/post_users.yaml')
    def post(self):
        data = Users.parser.parse_args()

        user_id = data.get('user_id')

        if id is not None and UsersModel.find_by_id(id):
            return {'message': "Ya existe un users con id '{}'.".format(id)}, 400

        users = UsersModel(**data)
        try:
            users.save_to_db()
        except Exception as e:
            logging.error('Ocurrió un error al crear Cliente.', exc_info=e)
            return {"message": "Ocurrió un error al crear Users."}, 500

        return users.json(), 201


class UsersSearch(Resource):

    @jwt_required
    @check('users_search')
    @swag_from('../swagger/users/search_users.yaml')
    def post(self):
        query = UsersModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'user_id', lambda x: UsersModel.user_id == x)
            query = restrict(query, filters, 'username', lambda x: UsersModel.username.contains(x))
            query = restrict(query, filters, 'password', lambda x: UsersModel.password.contains(x))
            query = restrict(query, filters, 'passkey', lambda x: UsersModel.passkey.contains(x))
            query = restrict(query, filters, 'uploaded', lambda x: UsersModel.uploaded == x)
            query = restrict(query, filters, 'downloaded', lambda x: UsersModel.downloaded == x)
        return paginated_results(query)
