import hashlib
import os
import pathlib
import shutil
from datetime import datetime

from flask import current_app
from flask_jwt_extended import get_jwt_identity
from werkzeug.utils import secure_filename

from models.torrent_file import TorrentFileModel


def get_filename_hash(filename):
    date = datetime.now()
    filename_split = filename.split('.')
    filename_hash = "{}_{}".format(".".join(filename_split[0:-1]), date.strftime("%Y%m%d_%H%M%S_%f"))
    if len(filename_split) > 1:
        filename_hash += "." + filename_split[-1]
    return filename_hash


def get_tmp_directory():
    path_string = str(os.path.join(current_app.config['UPLOAD_FOLDER'], current_app.config['TEMPORAL_FOLDER']))
    return create_or_get_path(path_string)


def get_file_directory(hash, module, date_time=None):
    if not date_time:
        date_time = datetime.today()
    year = date_time.strftime("%Y")
    month = date_time.strftime("%m")
    day = date_time.strftime("%d")
    path_string = str(os.path.join(current_app.config['UPLOAD_FOLDER'], year, month, day, hash, module))
    return create_or_get_path(path_string)


def create_or_get_path(path_string):
    path = pathlib.Path(path_string)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    return str(path)


# def move_file_to_final_destination(path_file, module):
#     # Get filename
#     separator = os.path.sep
#     path_string_split = path_file.split(separator)
#     filename = path_string_split[len(path_string_split) - 1]
#
#     # Get file location
#     path_string_dir_move = get_file_directory(module=module)
#
#     # Get path to move file
#     path_to_move_file = str(os.path.join(path_string_dir_move, filename))
#
#     # Get path for check existing file an folder to move
#     path_file = pathlib.Path(path_file)
#     path_move = pathlib.Path(path_string_dir_move)
#     if path_file.is_file() and path_move.is_dir():
#         os.rename(path_file, path_to_move_file)
#
#     return path_to_move_file


def delete_file(path_string):
    if os.path.exists(path_string):
        os.remove(path_string)


def delete_files_by_hash_datetime(hash, date_time):
    year = date_time.strftime("%Y")
    month = date_time.strftime("%m")
    day = date_time.strftime("%d")
    path_string = str(os.path.join(current_app.config['UPLOAD_FOLDER'], year, month, day, hash))
    if os.path.exists(path_string):
        shutil.rmtree(path_string)


def save_file(file, principal=None, hash=None, date_time=None):
    if not getattr(file, 'filename', None):
        return None

    original_filename = file.filename
    filename_clean = secure_filename(get_filename_hash(original_filename))
    mime_type = file.content_type
    module = 'OTHERS'
    if mime_type.find('image') != -1:
        module = 'IMAGE'
    if mime_type.find('bittorrent') != -1:
        module = 'TORRENT'
    file_path_destination = os.path.join(get_file_directory(module=module, hash=hash, date_time=date_time),
                                         filename_clean)

    # Write File on disk
    file_on_disk = open(file_path_destination, 'wb')
    shutil.copyfileobj(file, file_on_disk)
    file.close()
    file_on_disk.close()

    usuario = get_jwt_identity()
    torrent_file = TorrentFileModel(module=module, principal=principal, file_name=original_filename,
                                    mime_type=mime_type, path=file_path_destination, user_create=usuario,
                                    date_create=date_time)

    return torrent_file


def cheksum_file(file):
    if not getattr(file, 'filename', None):
        return None
    md5_hash = hashlib.md5()
    content = file.read()
    file.seek(0)
    md5_hash.update(content)
    digest = md5_hash.hexdigest()
    return digest


def save_system_file(file, module_folder):
    if not getattr(file, 'filename', None):
        return None

    original_filename = file.filename
    filename_clean = secure_filename(get_filename_hash(original_filename))
    file_path_destination = os.path.join(
        create_or_get_path(os.path.join(current_app.config['SYSTEM_FILES_FOLDER'], module_folder)), filename_clean)

    # Write File on disk
    file_on_disk = open(file_path_destination, 'wb')
    shutil.copyfileobj(file, file_on_disk)
    file.close()
    file_on_disk.close()

    return file_path_destination
