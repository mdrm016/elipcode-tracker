import logging
import os

import bencodepy
from torrentool.torrent import Torrent

from file_utils import get_tmp_directory

log = logging.getLogger(__name__)


def get_torrent_info(torrent_path):
    info_dict = dict()
    try:
        info = bencodepy.bdecode(open(torrent_path, 'rb').read())[b'info']
        info_dict['original_name'] = info[b'name'].decode()
        if b'files' in info:
            info_dict['total_length'] = 0
            info_dict['files'] = []
            for file in info[b'files']:
                info_dict['total_length'] += file[b'length']
                file_dict = dict()
                file_dict['length'] = file[b'length']
                path_array = []
                for path in file[b'path']:
                    path_array.append(path.decode())

                file_dict['path'] = path_array
                info_dict['files'].append(file_dict)
        else:
            # Only one file
            info_dict['total_length'] = info[b'length']
            info_dict['files'] = []
            file_dict = dict()
            file_dict['path'] = [info_dict['original_name']]
            file_dict['length'] = info_dict['total_length']

            info_dict['files'].append(file_dict)

    except Exception as e:
        log.error(str(e.__cause__))

    return info_dict


def set_torrent_announce(torrent_path, announce_url):
    torrent = Torrent.from_file(torrent_path)
    torrent.announce_urls = [announce_url]
    path = os.path.join(get_tmp_directory(), 'tmp_'+torrent_path.split(os.path.sep)[-1])
    torrent.to_file(path)
    return path
