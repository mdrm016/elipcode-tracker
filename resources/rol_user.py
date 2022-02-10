import logging

from flasgger import swag_from
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse
from models.rol_user import RolUserModel
from utils import restrict, check, paginated_results


class Principalmembers(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('d', type=int)
    parser.add_argument('rol_id', type=int)
    parser.add_argument('user_id', type=int)

    @jwt_required
    @check('principalmembers_get')
    @swag_from('../swagger/principalmembers/get_principalmembers.yaml')
    def get(self, id):
        rol_user = RolUserModel.find_by_rol_user_id(id)
        if rol_user:
            return rol_user.json()
        return {'message': 'No se encuentra rol_user'}, 404

    @jwt_required
    @check('principalmembers_update')
    @swag_from('../swagger/principalmembers/put_principalmembers.yaml')
    def put(self, id):
        rol_user = RolUserModel.find_by_rol_user_id(id)
        if rol_user:
            newdata = Principalmembers.parser.parse_args()
            rol_user.from_reqparse(newdata)
            rol_user.save_to_db()
            return rol_user.json()
        return {'message': 'No se encuentra rol_user'}, 404

    @jwt_required
    @check('principalmembers_delete')
    @swag_from('../swagger/principalmembers/delete_principalmembers.yaml')
    def delete(self, id):
        rol_user = RolUserModel.find_by_rol_user_id(id)
        if rol_user:
            rol_user.delete_from_db()

        return {'message': 'Se ha borrado rol_user'}


class PrincipalmembersList(Resource):

    @jwt_required
    @check('principalmembers_list')
    @swag_from('../swagger/principalmembers/list_principalmembers.yaml')
    def get(self):
        query = RolUserModel.query
        return paginated_results(query)

    @jwt_required
    @check('principalmembers_insert')
    @swag_from('../swagger/principalmembers/post_principalmembers.yaml')
    def post(self):
        data = Principalmembers.parser.parse_args()

        principalmembership_id = data.get('principalmembership_id')

        if id is not None and RolUserModel.find_by_rol_user_id(id):
            return {'message': "Ya existe un principalmembers con id '{}'.".format(id)}, 400

        principalmembers = RolUserModel(**data)
        try:
            principalmembers.save_to_db()
        except Exception as e:
            logging.error('Ocurrió un error al crear Cliente.', exc_info=e)
            return {"message": "Ocurrió un error al crear rol_user."}, 500

        return principalmembers.json(), 201


class PrincipalmembersSearch(Resource):

    @jwt_required
    @check('principalmembers_search')
    @swag_from('../swagger/principalmembers/search_principalmembers.yaml')
    def post(self):
        query = RolUserModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'id', lambda x: RolUserModel.principalmembership_id == x)
            query = restrict(query, filters, 'rol_id', lambda x: RolUserModel.principal_id == x)
            query = restrict(query, filters, 'user_id', lambda x: RolUserModel.user_id == x)
        return paginated_results(query)
