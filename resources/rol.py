from flasgger import swag_from
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse

from models.permission import PermissionModel
from models.rol import RolModel
from utils import restrict, check, paginated_results


class Rol(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('name', type=str)
    parser.add_argument('permissions', action='append')

    @jwt_required
    @check('rol_get')
    @swag_from('../swagger/principals/get_principals.yaml')
    def get(self, id):
        rol = RolModel.find_by_rol_id(id)
        if rol:
            return rol.json()
        return {'message': 'No se encuentra Principals'}, 404

    @jwt_required
    @check('rol_update')
    @swag_from('../swagger/principals/put_principals.yaml')
    def put(self, id):
        rol = RolModel.find_by_rol_id(id)
        if not rol:
            return {'error': 'Rol not found'}, 404

        newdata = Rol.parser.parse_args()
        rol.from_reqparse(newdata)
        # Link with permissions
        if 'permissions' in newdata and newdata['permissions'] is not None:
            rol.permissions.clear()
            for permission in newdata['permissions']:
                permissionModel = PermissionModel.query.filter_by(name=permission).first()
                if permissionModel:
                    rol.permissions.append(permissionModel)

        rol.save_to_db()
        return {'msg': 'Rol updated'}, 200


    @jwt_required
    @check('rol_delete')
    @swag_from('../swagger/principals/delete_principals.yaml')
    def delete(self, id):
        principals = RolModel.find_by_rol_id(id)
        if principals:
            principals.delete_from_db()

        return {'msg': 'Rol deleted'}


class RolList(Resource):

    @jwt_required
    @check('rol_list')
    @swag_from('../swagger/principals/list_principals.yaml')
    def get(self):
        query = RolModel.query
        return paginated_results(query)

    @jwt_required
    @check('rol_insert')
    @swag_from('../swagger/principals/post_principals.yaml')
    def post(self):
        data = Rol.parser.parse_args()

        id = data.get('principal_id')

        if id is not None and RolModel.find_by_rol_id(id):
            return {'error': "A role with id '{}' already exists.".format(id)}, 400

        # Link with permissions
        rol = RolModel(name=data.name)
        if 'permissions' in data and data['permissions'] is not None:
            for permission in data['permissions']:
                permissionModel = PermissionModel.query.filter_by(name=permission).first()
                if permissionModel:
                    rol.permissions.append(permissionModel)

        try:
            rol.save_to_db()
        except Exception as e:
            return {"error": "An error occurred while creating the rol"}, 500

        return {"msg": "Rol created"}, 201


class RolSearch(Resource):

    @jwt_required
    @check('rol_search')
    @swag_from('../swagger/principals/search_principals.yaml')
    def post(self):
        query = RolModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'id', lambda x: RolModel.id == x)
            query = restrict(query, filters, 'name', lambda x: RolModel.name.contains(x))
        return paginated_results(query)
