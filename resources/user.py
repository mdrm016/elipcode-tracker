from datetime import datetime

from flasgger import swag_from
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, reqparse

from models.peers import PeersModel
from models.rol import RolModel
from models.user import UserModel
from utils import restrict, check, paginated_results


class User(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int)
    parser.add_argument('username', type=str)
    parser.add_argument('password', type=str)
    parser.add_argument('status', type=str)
    parser.add_argument('rol', type=str)
    parser.add_argument('passkey', type=str)
    parser.add_argument('uploaded', type=int)
    parser.add_argument('downloaded', type=int)
    parser.add_argument('email', type=str)
    parser.add_argument('user_create', type=str)
    parser.add_argument('date_create', type=lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'))
    parser.add_argument('user_modifier', type=str)
    parser.add_argument('date_modifier', type=lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'))

    @jwt_required
    @check('user_get')
    @swag_from('../swagger/users/get_users.yaml')
    def get(self, id):
        user = UserModel.find_by_user_id(id)
        if user:
            return user.json()
        return {'error': 'User not found'}, 404

    @jwt_required
    @check('user_update')
    @swag_from('../swagger/users/put_users.yaml')
    def put(self, id):
        user = UserModel.find_by_user_id(id)
        if not user:
            return {'error': 'User not found'}, 404

        newdata = User.parser.parse_args()
        # user.from_reqparse(newdata)
        user.status = newdata['status']

        # Change the rol
        if user.roles[0].name != newdata['rol']:
            new_rol = RolModel.query.filter_by(name=newdata['rol']).first()
            if new_rol:
                user.roles.clear()
                user.roles.append(new_rol)

        user.save_to_db()
        return {'msg': 'User updated'}, 200

    @jwt_required
    @check('user_delete')
    @swag_from('../swagger/users/delete_users.yaml')
    def delete(self, id):
        user = UserModel.find_by_id(id)
        if user:
            user.delete_from_db()

        return {'msg': 'User deleted'}, 200


class UserList(Resource):

    @jwt_required
    @check('user_list')
    @swag_from('../swagger/users/list_users.yaml')
    def get(self):
        query = UserModel.query
        return paginated_results(query)

    @jwt_required
    @check('user_insert')
    @swag_from('../swagger/users/post_users.yaml')
    def post(self):
        data = User.parser.parse_args()
        id = data.get('user_id')

        if id is not None and UserModel.find_by_user_id(id):
            return {'error': "A user with id '{}' already exists".format(id)}, 400

        user = UserModel(**data)
        try:
            user.save_to_db()
        except Exception as e:
            return {"error": "An error occurred while creating the user."}, 500

        return {"msg": "User created."}, 201


class UserSearch(Resource):

    @jwt_required
    @check('user_search')
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
    @check('user_statistics')
    def get(self):
        username = get_jwt_identity()
        user = UserModel.query.filter_by(username=username).first()
        peers = PeersModel.query.filter_by(user_id=user.id).all()

        uploads = downloads = 0
        for peer in peers:
            if peer.seeding:
                uploads += 1
            else:
                downloads += 1

        if not user:
            return {'error': 'User not found'}, 404

        statistics = {
            'uploaded': user.uploaded,
            'downloaded': user.downloaded,
            'seed_bonus': 0,
            'downloads': downloads,
            'uploads': uploads
        }

        return statistics, 200
