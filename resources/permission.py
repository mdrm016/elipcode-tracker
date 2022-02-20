from flasgger import swag_from
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse
from models.permission import PermissionModel
from utils import restrict, check, paginated_results


class Permission(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('id', type=int)
    parser.add_argument('name', type=str)
    parser.add_argument('group', type=str)

    @jwt_required
    @check('permission_get')
    @swag_from('../swagger/permission/get_permission.yaml')
    def get(self, id):
        permission = PermissionModel.find_by_id(id)
        if permission:
            return permission.json(), 200
        return {'error': 'Permission not found'}, 404

    @jwt_required
    @check('permission_update')
    @swag_from('../swagger/permission/put_permission.yaml')
    def put(self, id):
        permission = PermissionModel.find_by_id(id)
        if permission:
            newdata = Permission.parser.parse_args()
            permission.from_reqparse(newdata)
            permission.save_to_db()
            return {'msg': 'Permission updated'}, 201
        return {'error': 'Permission not found'}, 404

    @jwt_required
    @check('permission_delete')
    @swag_from('../swagger/permission/delete_permission.yaml')
    def delete(self, id):
        permission = PermissionModel.find_by_id(id)
        if permission:
            permission.delete_from_db()

        return {'msg': 'Permission deleted'}


class PermissionList(Resource):

    @jwt_required
    @check('permission_list')
    @swag_from('../swagger/permission/list_permission.yaml')
    def get(self):
        query = PermissionModel.query
        permissions = [x.json() for x in query.all()]
        return permissions

    @jwt_required
    @check('permission_insert')
    @swag_from('../swagger/permission/post_permission.yaml')
    def post(self):
        data = Permission.parser.parse_args()

        id = data.get('id')

        if id is not None and PermissionModel.find_by_id(id):
            return {'message': "Ya existe un permission con id '{}'.".format(id)}, 400

        permission = PermissionModel(**data)
        try:
            permission.save_to_db()
        except Exception as e:
            return {"error": "A error ocurred to create the permission: {}".format(e.__cause__)}, 500

        return {"msg": "Permisssion created"}, 201


class PermissionSearch(Resource):

    @jwt_required
    @check('permission_search')
    @swag_from('../swagger/permission/search_permission.yaml')
    def post(self):
        query = PermissionModel.query
        if request.json:
            filters = request.json
            query = restrict(query, filters, 'id', lambda x: PermissionModel.id == x)
            query = restrict(query, filters, 'name', lambda x: PermissionModel.name.contains(x))
            query = restrict(query, filters, 'group', lambda x: PermissionModel.group.contains(x))
        return paginated_results(query)
