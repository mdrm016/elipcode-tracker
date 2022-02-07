import base64
import logging
from datetime import datetime

from flasgger import swag_from
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse
from models.principalmembers import PrincipalmembersModel
from utils import restrict, check, paginated_results


class Principalmembers(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('principalmembership_id', type=int)
    parser.add_argument('principal_id', type=int)
    parser.add_argument('user_id', type=int)

    @jwt_required
    @check('principalmembers_get')
    @swag_from('../swagger/principalmembers/get_principalmembers.yaml')
    def get(self, id):
        principalmembers = PrincipalmembersModel.find_by_id(id)
        if principalmembers:
            return principalmembers.json()
        return {'message': 'No se encuentra Principalmembers'}, 404

    @jwt_required
    @check('principalmembers_update')
    @swag_from('../swagger/principalmembers/put_principalmembers.yaml')
    def put(self, id):
        principalmembers = PrincipalmembersModel.find_by_id(id)
        if principalmembers:
            newdata = Principalmembers.parser.parse_args()
            principalmembers.from_reqparse(newdata)
            principalmembers.save_to_db()
            return principalmembers.json()
        return {'message': 'No se encuentra Principalmembers'}, 404

    @jwt_required
    @check('principalmembers_delete')
    @swag_from('../swagger/principalmembers/delete_principalmembers.yaml')
    def delete(self, id):
        principalmembers = PrincipalmembersModel.find_by_id(id)
        if principalmembers:
            principalmembers.delete_from_db()

        return {'message': 'Se ha borrado Principalmembers'}


class PrincipalmembersList(Resource):

    @jwt_required
    @check('principalmembers_list')
    @swag_from('../swagger/principalmembers/list_principalmembers.yaml')
    def get(self):
        query = PrincipalmembersModel.query
        return paginated_results(query)

    @jwt_required
    @check('principalmembers_insert')
    @swag_from('../swagger/principalmembers/post_principalmembers.yaml')
    def post(self):
        data = Principalmembers.parser.parse_args()

        principalmembership_id = data.get('principalmembership_id')

        if id is not None and PrincipalmembersModel.find_by_id(id):
            return {'message': "Ya existe un principalmembers con id '{}'.".format(id)}, 400

        principalmembers = PrincipalmembersModel(**data)
        try:
            principalmembers.save_to_db()
        except Exception as e:
            logging.error('Ocurrió un error al crear Cliente.', exc_info=e)
            return {"message": "Ocurrió un error al crear Principalmembers."}, 500

        return principalmembers.json(), 201


class PrincipalmembersSearch(Resource):

    @jwt_required
    @check('principalmembers_search')
    @swag_from('../swagger/principalmembers/search_principalmembers.yaml')
    def post(self):
        query = PrincipalmembersModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'principalmembership_id', lambda x: PrincipalmembersModel.principalmembership_id == x)
            query = restrict(query, filters, 'principal_id', lambda x: PrincipalmembersModel.principal_id == x)
            query = restrict(query, filters, 'user_id', lambda x: PrincipalmembersModel.user_id == x)
        return paginated_results(query)
