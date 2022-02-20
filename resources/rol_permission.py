import base64
import logging
from datetime import datetime

from flasgger import swag_from
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse
from models.rol_permission import RolPermissionModel
from utils import restrict, check, paginated_results


class RolPermission(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int)
    parser.add_argument('rol_id', type=int)
    parser.add_argument('permission_id', type=int)

    @jwt_required
    @check('rol_permission_get')
    @swag_from('../swagger/rol_permission/get_rol_permission.yaml')
    def get(self, id):
        rol_permission = RolPermissionModel.find_by_id(id)
        if rol_permission:
            return rol_permission.json()
        return {'message': 'No se encuentra Rol Permission'}, 404

    @jwt_required
    @check('rol_permission_update')
    @swag_from('../swagger/rol_permission/put_rol_permission.yaml')
    def put(self, id):
        rol_permission = RolPermissionModel.find_by_id(id)
        if rol_permission:
            newdata = RolPermission.parser.parse_args()
            rol_permission.from_reqparse(newdata)
            rol_permission.save_to_db()
            return rol_permission.json()
        return {'message': 'No se encuentra Rol Permission'}, 404

    @jwt_required
    @check('rol_permission_delete')
    @swag_from('../swagger/rol_permission/delete_rol_permission.yaml')
    def delete(self, id):
        rol_permission = RolPermissionModel.find_by_id(id)
        if rol_permission:
            rol_permission.delete_from_db()

        return {'message': 'Se ha borrado Rol Permission'}


class RolPermissionList(Resource):

    @jwt_required
    @check('rol_permission_list')
    @swag_from('../swagger/rol_permission/list_rol_permission.yaml')
    def get(self):
        query = RolPermissionModel.query
        return paginated_results(query)

    @jwt_required
    @check('rol_permission_insert')
    @swag_from('../swagger/rol_permission/post_rol_permission.yaml')
    def post(self):
        data = RolPermission.parser.parse_args()

        id = data.get('id')

        if id is not None and RolPermissionModel.find_by_id(id):
            return {'message': "Ya existe un rol_permission con id '{}'.".format(id)}, 400

        rol_permission = RolPermissionModel(**data)
        try:
            rol_permission.save_to_db()
        except Exception as e:
            logging.error('Ocurrió un error al crear Cliente.', exc_info=e)
            return {"message": "Ocurrió un error al crear Rol Permission."}, 500

        return rol_permission.json(), 201


class RolPermissionSearch(Resource):

    @jwt_required
    @check('rol_permission_search')
    @swag_from('../swagger/rol_permission/search_rol_permission.yaml')
    def post(self):
        query = RolPermissionModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'id', lambda x: RolPermissionModel.id == x)
            query = restrict(query, filters, 'rol_id', lambda x: RolPermissionModel.rol_id == x)
            query = restrict(query, filters, 'permission_id', lambda x: RolPermissionModel.permission_id == x)
        return paginated_results(query)
