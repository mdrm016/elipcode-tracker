import datetime
import os
import pathlib

from flask import current_app


def get_filename_hash(filename):
    date = datetime.datetime.now()
    filename_split = filename.split('.')
    filename_hash = "{}_{}".format(".".join(filename_split[0:-1]), date.strftime("%Y%m%d_%H%M%S_%f"))
    if len(filename_split) > 1:
        filename_hash += "." + filename_split[-1]
    return filename_hash


def get_tmp_directory():
    path_string = str(os.path.join(current_app.config['UPLOAD_FOLDER'], current_app.config['TEMPORAL_FOLDER']))
    return create_or_get_path(path_string)


def get_file_directory(module):
    date = datetime.datetime.now()
    year = date.strftime("%Y")
    month = date.strftime("%m")
    day = date.strftime("%d")
    path_string = str(
        os.path.join(current_app.config['UPLOAD_FOLDER'], module, year, month, day))
    return create_or_get_path(path_string)


def create_or_get_path(path_string):
    path = pathlib.Path(path_string)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    return str(path)


def move_file_to_final_destination(path_file, module):
    # Get filename
    separator = os.path.sep
    path_string_split = path_file.split(separator)
    filename = path_string_split[len(path_string_split) - 1]

    # Get file location
    path_string_dir_move = get_file_directory(module)

    # Get path to move file
    path_to_move_file = str(os.path.join(path_string_dir_move, filename))

    # Get path for check existing file an folder to move
    path_file = pathlib.Path(path_file)
    path_move = pathlib.Path(path_string_dir_move)
    if path_file.is_file() and path_move.is_dir():
        os.rename(path_file, path_to_move_file)

    return path_to_move_file


def delete_file(path_string):
    if os.path.exists(path_string):
        os.remove(path_string)