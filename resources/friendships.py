import logging

from flasgger import swag_from
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse
from models.friendships import FriendshipsModel
from utils import restrict, check, paginated_results


class Friendships(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('friendship_id', type=int)
    parser.add_argument('userone_id', type=int)
    parser.add_argument('usertwo_id', type=int)
    parser.add_argument('accepted', type=bool)

    @jwt_required
    @check('friendships_get')
    @swag_from('../swagger/friendships/get_friendships.yaml')
    def get(self, id):
        friendships = FriendshipsModel.find_by_id(id)
        if friendships:
            return friendships.json()
        return {'message': 'No se encuentra Friendships'}, 404

    @jwt_required
    @check('friendships_update')
    @swag_from('../swagger/friendships/put_friendships.yaml')
    def put(self, id):
        friendships = FriendshipsModel.find_by_id(id)
        if friendships:
            newdata = Friendships.parser.parse_args()
            friendships.from_reqparse(newdata)
            friendships.save_to_db()
            return friendships.json()
        return {'message': 'No se encuentra Friendships'}, 404

    @jwt_required
    @check('friendships_delete')
    @swag_from('../swagger/friendships/delete_friendships.yaml')
    def delete(self, id):
        friendships = FriendshipsModel.find_by_id(id)
        if friendships:
            friendships.delete_from_db()

        return {'message': 'Se ha borrado Friendships'}


class FriendshipsList(Resource):

    @jwt_required
    @check('friendships_list')
    @swag_from('../swagger/friendships/list_friendships.yaml')
    def get(self):
        query = FriendshipsModel.query
        return paginated_results(query)

    @jwt_required
    @check('friendships_insert')
    @swag_from('../swagger/friendships/post_friendships.yaml')
    def post(self):
        data = Friendships.parser.parse_args()

        friendship_id = data.get('friendship_id')

        if id is not None and FriendshipsModel.find_by_id(id):
            return {'message': "Ya existe un friendships con id '{}'.".format(id)}, 400

        friendships = FriendshipsModel(**data)
        try:
            friendships.save_to_db()
        except Exception as e:
            logging.error('Ocurrió un error al crear Cliente.', exc_info=e)
            return {"message": "Ocurrió un error al crear Friendships."}, 500

        return friendships.json(), 201


class FriendshipsSearch(Resource):

    @jwt_required
    @check('friendships_search')
    @swag_from('../swagger/friendships/search_friendships.yaml')
    def post(self):
        query = FriendshipsModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'friendship_id', lambda x: FriendshipsModel.friendship_id == x)
            query = restrict(query, filters, 'userone_id', lambda x: FriendshipsModel.userone_id == x)
            query = restrict(query, filters, 'usertwo_id', lambda x: FriendshipsModel.usertwo_id == x)
            query = restrict(query, filters, 'accepted', lambda x: x)
        return paginated_results(query)
