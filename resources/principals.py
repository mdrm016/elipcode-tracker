import base64
import logging
from datetime import datetime

from flasgger import swag_from
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse
from models.principals import PrincipalsModel
from utils import restrict, check, paginated_results


class Principals(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('principal_id', type=int)
    parser.add_argument('principal_name', type=str)

    @jwt_required
    @check('principals_get')
    @swag_from('../swagger/principals/get_principals.yaml')
    def get(self, id):
        principals = PrincipalsModel.find_by_id(id)
        if principals:
            return principals.json()
        return {'message': 'No se encuentra Principals'}, 404

    @jwt_required
    @check('principals_update')
    @swag_from('../swagger/principals/put_principals.yaml')
    def put(self, id):
        principals = PrincipalsModel.find_by_id(id)
        if principals:
            newdata = Principals.parser.parse_args()
            principals.from_reqparse(newdata)
            principals.save_to_db()
            return principals.json()
        return {'message': 'No se encuentra Principals'}, 404

    @jwt_required
    @check('principals_delete')
    @swag_from('../swagger/principals/delete_principals.yaml')
    def delete(self, id):
        principals = PrincipalsModel.find_by_id(id)
        if principals:
            principals.delete_from_db()

        return {'message': 'Se ha borrado Principals'}


class PrincipalsList(Resource):

    @jwt_required
    @check('principals_list')
    @swag_from('../swagger/principals/list_principals.yaml')
    def get(self):
        query = PrincipalsModel.query
        return paginated_results(query)

    @jwt_required
    @check('principals_insert')
    @swag_from('../swagger/principals/post_principals.yaml')
    def post(self):
        data = Principals.parser.parse_args()

        principal_id = data.get('principal_id')

        if id is not None and PrincipalsModel.find_by_id(id):
            return {'message': "Ya existe un principals con id '{}'.".format(id)}, 400

        principals = PrincipalsModel(**data)
        try:
            principals.save_to_db()
        except Exception as e:
            logging.error('Ocurrió un error al crear Cliente.', exc_info=e)
            return {"message": "Ocurrió un error al crear Principals."}, 500

        return principals.json(), 201


class PrincipalsSearch(Resource):

    @jwt_required
    @check('principals_search')
    @swag_from('../swagger/principals/search_principals.yaml')
    def post(self):
        query = PrincipalsModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'principal_id', lambda x: PrincipalsModel.principal_id == x)
            query = restrict(query, filters, 'principal_name', lambda x: PrincipalsModel.principal_name.contains(x))
        return paginated_results(query)
