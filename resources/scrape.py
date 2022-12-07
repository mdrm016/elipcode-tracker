from urllib.parse import urlparse, parse_qsl

from flask import request
from flask_restful import Resource, reqparse

from utils import tracker_response


class Scrape(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('passkey', type=str)

    def get(self, passkey):
        """
        Returns the list of seeds, peers and downloads a torrent info_hash has, according to the specified tracker
        Args:
            tracker (str): The announce url for a tracker, usually taken directly from the torrent metadata
            hashes (list): A list of torrent info_hash's to query the tracker for
        Returns:
            A dict of dicts. The key is the torrent info_hash's from the 'hashes' parameter,
            and the value is a dict containing "seeds", "peers" and "complete".
            Eg:
            {
                "2d88e693eda7edf3c1fd0c48e8b99b8fd5a820b2" : { "seeds" : "34", "peers" : "189", "complete" : "10" },
                "8929b29b83736ae650ee8152789559355275bd5c" : { "seeds" : "12", "peers" : "0", "complete" : "290" }
            }
        """
        parse_url = urlparse(request.url)
        query_dict = dict(parse_qsl(parse_url.query, encoding='latin_1'))

        # TODO: implementar

        print(query_dict)

        response_dict = {'files': {}}
        response_dict['files']['a_hash'] = {
            'complete': 0,
            'downloaded': 0,
            'incomplete': 0
        }
        return tracker_response(response_dict)
