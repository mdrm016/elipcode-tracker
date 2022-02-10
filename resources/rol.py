import base64
import logging
from datetime import datetime

from flasgger import swag_from
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse
from models.rol import RolModel
from utils import restrict, check, paginated_results


class Principals(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int)
    parser.add_argument('name', type=str)

    @jwt_required
    @check('principals_get')
    @swag_from('../swagger/principals/get_principals.yaml')
    def get(self, id):
        rol = RolModel.find_by_rol_id(id)
        if rol:
            return rol.json()
        return {'message': 'No se encuentra Principals'}, 404

    @jwt_required
    @check('principals_update')
    @swag_from('../swagger/principals/put_principals.yaml')
    def put(self, id):
        rol = RolModel.find_by_rol_id(id)
        if rol:
            newdata = Principals.parser.parse_args()
            rol.from_reqparse(newdata)
            rol.save_to_db()
            return rol.json()
        return {'message': 'No se encuentra Principals'}, 404

    @jwt_required
    @check('principals_delete')
    @swag_from('../swagger/principals/delete_principals.yaml')
    def delete(self, id):
        principals = RolModel.find_by_rol_id(id)
        if principals:
            principals.delete_from_db()

        return {'message': 'Se ha borrado Principals'}


class PrincipalsList(Resource):

    @jwt_required
    @check('principals_list')
    @swag_from('../swagger/principals/list_principals.yaml')
    def get(self):
        query = RolModel.query
        return paginated_results(query)

    @jwt_required
    @check('principals_insert')
    @swag_from('../swagger/principals/post_principals.yaml')
    def post(self):
        data = Principals.parser.parse_args()

        principal_id = data.get('principal_id')

        if id is not None and RolModel.find_by_rol_id(id):
            return {'message': "Ya existe un principals con id '{}'.".format(id)}, 400

        rol = RolModel(**data)
        try:
            rol.save_to_db()
        except Exception as e:
            logging.error('Ocurrió un error al crear Cliente.', exc_info=e)
            return {"message": "Ocurrió un error al crear Principals."}, 500

        return rol.json(), 201


class PrincipalsSearch(Resource):

    @jwt_required
    @check('principals_search')
    @swag_from('../swagger/principals/search_principals.yaml')
    def post(self):
        query = RolModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'id', lambda x: RolModel.id == x)
            query = restrict(query, filters, 'name', lambda x: RolModel.name.contains(x))
        return paginated_results(query)
