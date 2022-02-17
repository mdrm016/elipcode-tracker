import base64
import logging
from datetime import datetime

from flasgger import swag_from
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, reqparse
from models.user import UserModel
from utils import restrict, check, paginated_results


class User(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int)
    parser.add_argument('username', type=str)
    parser.add_argument('password', type=str)
    parser.add_argument('passkey', type=str)
    parser.add_argument('uploaded', type=int)
    parser.add_argument('downloaded', type=int)
    parser.add_argument('email', type=str)
    parser.add_argument('user_create', type=str)
    parser.add_argument('date_create', type=lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'))

    @jwt_required
    @check('users_get')
    @swag_from('../swagger/users/get_users.yaml')
    def get(self, id):
        user = UserModel.find_by_user_id(id)
        if user:
            return user.json()
        return {'message': 'User not found'}, 404

    @jwt_required
    @check('users_update')
    @swag_from('../swagger/users/put_users.yaml')
    def put(self, id):
        user = UserModel.find_by_user_id(id)
        if user:
            newdata = User.parser.parse_args()
            user.from_reqparse(newdata)
            user.save_to_db()
            return user.json()
        return {'message': 'User not found'}, 404

    @jwt_required
    @check('users_delete')
    @swag_from('../swagger/users/delete_users.yaml')
    def delete(self, id):
        user = UserModel.find_by_id(id)
        if user:
            user.delete_from_db()

        return {'message': 'Se ha borrado Users'}


class UserList(Resource):

    @jwt_required
    @check('users_list')
    @swag_from('../swagger/users/list_users.yaml')
    def get(self):
        query = UserModel.query
        return paginated_results(query)

    @jwt_required
    @check('users_insert')
    @swag_from('../swagger/users/post_users.yaml')
    def post(self):
        data = User.parser.parse_args()
        user_id = data.get('user_id')

        if id is not None and UserModel.find_by_user_id(id):
            return {'message': "Ya existe un users con id '{}'.".format(id)}, 400

        user = UserModel(**data)
        try:
            user.save_to_db()
        except Exception as e:
            logging.error('Ocurrió un error al crear Cliente.', exc_info=e)
            return {"error": "An error occurred while creating the user."}, 500

        return {"msg": "User created."}, 201


class UserSearch(Resource):

    @jwt_required
    @check('users_search')
    @swag_from('../swagger/users/search_users.yaml')
    def post(self):
        query = UserModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'id', lambda x: UserModel.id == x)
            query = restrict(query, filters, 'username', lambda x: UserModel.username.contains(x))
            query = restrict(query, filters, 'password', lambda x: UserModel.password.contains(x))
            query = restrict(query, filters, 'passkey', lambda x: UserModel.passkey.contains(x))
            query = restrict(query, filters, 'uploaded', lambda x: UserModel.uploaded == x)
            query = restrict(query, filters, 'downloaded', lambda x: UserModel.downloaded == x)
            query = restrict(query, filters, 'user_create', lambda x: UserModel.user_create == x)
            query = restrict(query, filters, 'date_create', lambda x: UserModel.date_create == x)
        return paginated_results(query)


class UserStatistics(Resource):

    @jwt_required
    # @check('user_statistics')
    def get(self):
        username = get_jwt_identity()
        usuario = UserModel.query.filter_by(username=username).first()

        if not usuario:
            return {'error': 'User not found'}, 404

        statistics = {
            'uploaded': usuario.uploaded,
            'downloaded': usuario.downloaded,
            'seed_bonus': 0,
            'downloads': 0,
            'uploads': 0
        }

        return statistics, 200
