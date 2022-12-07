from resources.rol_permission import RolPermission, RolPermissionList, RolPermissionSearch
from resources.permission import Permission, PermissionList, PermissionSearch
from resources.scrape import Scrape
from resources.torrent_category import TorrentCategory, TorrentCategoryList, TorrentCategorySearch
import datetime

from models.rol import RolModel
from models.user import UserModel
from resources.announce import Announce, AnnounceMetadata
from resources.torrent import Torrents, TorrentsList, TorrentsSearch, TorrentFiles
from resources.friendships import Friendships, FriendshipsList, FriendshipsSearch
from resources.peers import Peers, PeersList, PeersSearch
from resources.rol_user import RolUser, RolUserList, RolUserSearch
from resources.user import User, UserList, UserSearch, UserStatistics
from resources.rol import Rol, RolList, RolSearch
from resources.category import Category, CategoryList, CategorySearch
from resources.torrent_file import TorrentFile, TorrentFileList, TorrentFileSearch
import os
from db import db
from flasgger import Swagger, swag_from
from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity,
    get_raw_jwt)
from flask_restful import Api
from utils import JSONEncoder, JSONDecoder

permisions = [
    'rol_permission_list',
    'rol_permission_search',
    'rol_permission_get',
    'rol_permission_insert',
    'rol_permission_update',
    'rol_permission_delete',
    'torrent_file_list',
    'torrent_file_search',
    'torrent_file_get',
    'torrent_file_insert',
    'torrent_file_update',
    'torrent_file_delete',
]

PREFIX_STORAGE = os.environ.get('PREFIX_STORAGE_PATH', '/media')
app = Flask(__name__, static_folder='static', static_url_path=f'{PREFIX_STORAGE}/static')
CORS(app, supports_credentials=True)
api = Api(app, errors={
    'NoAuthorizationError': {
        "message": "Request does not contain an access token.",
        'error': 'authorization_required',
        'status': 401
    }
})

app.config['RESTFUL_JSON'] = {'cls': JSONEncoder}
app.json_encoder = JSONEncoder
app.json_decoder = JSONDecoder


@app.errorhandler(404)
def handle_auth_error(e):
    return jsonify({
        "description": "You seem lost...",
        'error': 'resource_not_found'
    }), 404


@app.errorhandler(400)
def handle_auth_error(e):
    return jsonify({
        "description": "I don't understand this, please send it right.. appreciated!",
        'error': 'bad_request'
    }), 404


# Function to facilitate the app configuration from environment variables
def env_config(name, default):
    app.config[name] = os.environ.get(name, default=default)


PREFIX = os.environ.get('PREFIX_PATH', '/api')

# Database config
env_config('SQLALCHEMY_DATABASE_URI', 'postgresql://postgres:postgres@localhost:5432/bm_tracker')
# app.config['SQLALCHEMY_BINDS'] = {
#     'anotherdb':        'postgresql://postgres:postgres@localhost:5432/anotherdb'
# }
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['SQLALCHEMY_ECHO'] = False

# Swagger config
app.config['SWAGGER'] = {
    'title': 'elipcode-tracker',
    'version': '2.0.0',
    'description': 'API de servicios REST en Flask',
    'uiversion': 2,
    'tags': [{'name': 'jwt'}]
}
swagger = Swagger(app)


@app.after_request
def after_request(response):
    current_user = get_jwt_identity()
    # logger_audit.info(f'{current_user}: #{request.method} - #{request.path} args: {request.args.to_dict()} json: {response.json}')
    return response


# Tracker enviroment variables
app.config['TRACKER_ID'] = 'Elipcode'
app.config['ANNOUNCE_DOMAIN'] = 'http://192.168.100.2:5000'
app.config['USER_SECRET_KEY'] = 'e4cba2d5b70f412896117265'
app.config['UPLOAD_TMP_FOLDER'] = 'static/tmp'
app.config['UPLOAD_FOLDER'] = 'static/storage'
app.config['TORRENT_FILES_PREFIX'] = '[BodyMuscle-tracker.net]'
app.config['SYSTEM_FILES_FOLDER'] = 'static/system'

# Setup the Flask-JWT-Extended extension
app.config['JWT_SECRET_KEY'] = 'super-secret'
app.config['JWT_ERROR_MESSAGE_KEY'] = 'error'
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
jwt = JWTManager(app)

# tokens blacklist (replace this with database table or a redis cluster in production)
blacklist = set()


# Change this to get permissions from your permission store (database, redis, cache, file, etc.)
@jwt.user_claims_loader
def add_claims_to_access_token(identity):
    user = UserModel.query.filter_by(username=identity).first()
    user_rol = user.roles.pop()
    user_permissions = [x.name for x in user_rol.permissions]
    return {
        'rol': user_rol.name,
        'permissions': user_permissions
    }


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return jti in blacklist


######################
# Application routes #
######################

@app.route('/')
@app.route(f'{PREFIX}')
def welcome():
    return redirect("/apidocs", code=302)


# Provide a method to create access tokens. The create_access_token()
# function is used to actually generate the token, and you can return
# it to the caller however you choose.
@app.route(f'{PREFIX}/login', methods=['POST'])
@swag_from('swagger/flask_jwt_extended/login.yaml')
def login():
    if not request.is_json:
        return jsonify({"error": "Bad request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if not username or not password:
        return jsonify({"error": "Bad username or password. Please, enter the necesary fields"}), 400

    user = UserModel.get_by_username_and_password(username, password)

    if not user:
        return jsonify({"error": "User not exist or password incorrect, please, check your credentials"}), 401

    # Identity can be any data that is json serializable
    expires = datetime.timedelta(days=1)
    access_token = create_access_token(identity=username, expires_delta=expires)
    return jsonify(access_token=access_token), 200


@app.route(f'{PREFIX}/register', methods=['POST'])
@swag_from('swagger/flask_jwt_extended/register.yaml')
def register():
    if not request.is_json:
        return jsonify({"error": "Bad request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)
    email = request.json.get('email', None)
    if not username or not password or not email:
        return jsonify({"error": "Bad username, password or email. Please, complete the necesary fields"}), 400

    user = UserModel(username=username, password=password, email=email, status='active', user_create='admin',
                     date_create=datetime.datetime.now())
    rol = RolModel.query.filter_by(name='user').first()
    if rol is None:
        r = RolModel(name='user')
        r.save_to_db()
        rol = r

    user.roles.append(rol)
    user.save_to_db()

    # Identity can be any data that is json serializable
    user_passkey = user.passkey
    return jsonify({"msg": "Your user has been created! Passkey = " + user_passkey}), 200


@app.route(f'{PREFIX}/logout', methods=['DELETE'])
@jwt_required
@swag_from('swagger/flask_jwt_extended/logout.yaml')
def logout():
    jti = get_raw_jwt()['jti']
    blacklist.add(jti)
    return jsonify({"msg": "Successfully logged out"}), 200


# Protect a view with jwt_required, which requires a valid access token
# in the request to access.
@app.route(f'{PREFIX}/protected', methods=['GET'])
@jwt_required
@swag_from('swagger/protected/example.yaml')
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


api.add_resource(Category, f'{PREFIX}/category/<id>')
api.add_resource(CategoryList, f'{PREFIX}/category')
api.add_resource(CategorySearch, f'{PREFIX}/search/category')

api.add_resource(Rol, f'{PREFIX}/rol/<id>')
api.add_resource(RolList, f'{PREFIX}/rol')
api.add_resource(RolSearch, f'{PREFIX}/search/rol')

api.add_resource(User, f'{PREFIX}/user/<id>')
api.add_resource(UserList, f'{PREFIX}/user')
api.add_resource(UserSearch, f'{PREFIX}/search/user')
api.add_resource(UserStatistics, f'{PREFIX}/user/statistics')

api.add_resource(RolUser, f'{PREFIX}/rol_user/<id>')
api.add_resource(RolUserList, f'{PREFIX}/rol_user')
api.add_resource(RolUserSearch, f'{PREFIX}/search/rol_user')

api.add_resource(Peers, f'{PREFIX}/peers/<id>')
api.add_resource(PeersList, f'{PREFIX}/peers')
api.add_resource(PeersSearch, f'{PREFIX}/search/peers')

api.add_resource(Friendships, f'{PREFIX}/friendships/<friendship_id>')
api.add_resource(FriendshipsList, f'{PREFIX}/friendships')
api.add_resource(FriendshipsSearch, f'{PREFIX}/search/friendships')

api.add_resource(Torrents, f'{PREFIX}/torrents/<id>')
api.add_resource(TorrentsList, f'{PREFIX}/torrents')
api.add_resource(TorrentsSearch, f'{PREFIX}/search/torrents')
api.add_resource(TorrentFiles, f'{PREFIX}/torrents/get_torrent_file/<id>')

api.add_resource(Announce, '/<passkey>/announce')
api.add_resource(Scrape, '/<passkey>/scrape')
api.add_resource(AnnounceMetadata, f'{PREFIX}/get_announce')

api.add_resource(TorrentFile, '/torrent_file/<id>')
api.add_resource(TorrentFileList, '/torrent_file')
api.add_resource(TorrentFileSearch, '/search/torrent_file')

api.add_resource(TorrentCategory, '/torrent_category/<id>')
api.add_resource(TorrentCategoryList, '/torrent_category')
api.add_resource(TorrentCategorySearch, '/search/torrent_category')

api.add_resource(Permission, f'{PREFIX}/permission/<id>')
api.add_resource(PermissionList, f'{PREFIX}/permission')
api.add_resource(PermissionSearch, f'{PREFIX}/search/permission')

api.add_resource(RolPermission, f'{PREFIX}/rol_permission/<id>')
api.add_resource(RolPermissionList, f'{PREFIX}/rol_permission')
api.add_resource(RolPermissionSearch, f'{PREFIX}/search/rol_permission')

if __name__ == '__main__':
    db.init_app(app)
    app.run(host=os.environ.get("FLASK_HOST", default="0.0.0.0"), port=os.environ.get("FLASK_PORT", default=5000))
# this lines are required for debugging with pycharm (although you can delete them if you want)
else:
    db.init_app(app)
