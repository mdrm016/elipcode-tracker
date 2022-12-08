import time
from functools import wraps
import datetime
import decimal
import hashlib
from urllib.parse import urlparse, parse_qsl

from bencode import bencode
from flask import request, Response
from flask.json import JSONEncoder, JSONDecoder
# Define custom JSONEncoder for the ISO Datetime format
from flask_jwt_extended import get_jwt_identity, get_jwt_claims
from flask_restful.reqparse import Namespace
from json.decoder import WHITESPACE

settings = {
    'time_until_inactive': 30 * 60,  # 30 minutes
    'seed_interval': 300,  # 5 minutes
    'peer_interval': 30,  # 30 seconds
    'numwant_default': 30,  # 30 should be plent as stated by spec
    'compact_default': 0,  # 1 for bandwidth, 0 for compatability
    'no_peer_id_default': 0,  # 1 for bandwidth, 0 for compatability

    # Don't change these. I mean you can but its pointless
    'seed': 'S',
    'peer': 'P',
}


class JSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime.date):
                return obj.isoformat()
            elif isinstance(obj, decimal.Decimal):
                return float(obj)
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


class JSONDecoder(JSONDecoder):
    unicode_replacements = {
        '\u2018': "'", '\u2019': "'"
    }

    def __init__(self, *args, **kwargs):
        self.orig_obj_hook = kwargs.pop("object_hook", None)
        super(JSONDecoder, self).__init__(*args, object_hook=self.custom_obj_hook, strict=False, **kwargs)

    def decode(self, s, _w=WHITESPACE.match):
        for rk in self.unicode_replacements.keys():
            s = s.replace(rk, self.unicode_replacements.get(rk))
        # if max(s) > u'\u00FF':
        #     print(f'Unicode out of range in {s.index(max(s))}. Deleting that character and continuing')
        return super().decode(s, _w)

    def custom_obj_hook(self, dct):
        # Calling custom decode function:4
        if self.orig_obj_hook:  # Do we have another hook to call?
            return self.orig_obj_hook(dct)  # Yes: then do it
        return dct  # No: just return the decoded dict


# return a long representations of the current time in milliseconds
def current_time_milliseconds():
    return int(round(time.time() * 1000))


# Generate a 'unique' md5 hash adding the current time in milliseconds
# to a string
def unique_md5(string: str):
    m = hashlib.md5()
    m.update(f'{current_time_milliseconds()}{string}'.encode())
    return m.hexdigest()


# Utility function to only execute and assigment to an object if the value from a reqparse.Namespace dict is not None
def _assign_if_something(obj: object, newdata: Namespace, key: str):
    value = newdata.get(key)
    if value is not None:
        obj.__setattr__(key, value)


# Apply filter restrictions
def restrict(query, filters, name, condition):
    f = filters.get(name)
    if f:
        query = query.filter(condition(f))
    return query


# Encrypt password
def sha1_pass(text: str):
    m = hashlib.sha1()
    m.update(text.encode('utf-8'))
    d = m.digest()
    t = ''
    for aux in d:
        c: int = aux & 0xff
        hs = '{:02x}'.format(c)
        t += hs
    return t


def check(permision):
    def wrfunc(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            usuario = get_jwt_identity()
            if usuario is None:
                return {'message': 'No tiene permisos para realizar esta acción'}, 401
            claims = get_jwt_claims()
            if permision not in claims['permissions']:
                return {'message': 'No tiene permisos para realizar esta acción'}, 401
            return fn(*args, **kwargs)

        return wrapper

    return wrfunc


def paginated_results(query):
    pagination = request.args.get('pagination', 'true', str)
    jsondepth = request.args.get('jsondepth', 1, int)
    if pagination == 'true':
        paginated = query.paginate(page=request.args.get('page', 1, int))
        return {
            'page': paginated.page,
            'pages': paginated.pages,
            'items': [x.json(jsondepth) if jsondepth else x.json() for x in paginated.items]
        }
    else:
        return [x.json(jsondepth) if jsondepth else x.json() for x in query.all()]


# toHex = lambda x: "".join([hex(ord(c))[2:].zfill(2) for c in x])
# toHex = lambda x: "".join(["{:02X}".format(ord(c)) for c in x])
# Codificación hexadecimal
def to_hex(x):
    arr = []
    for c in x:
        try:
            coded = c.encode('latin_1')
            a = ord(c)
            b = hex(a)
            d = b[2:]
            e = d.zfill(2)
        except UnicodeEncodeError:
            byteString = c.encode('utf-8')
            e = ''.join('{:02x}'.format(x) for x in byteString)
        arr.append(e)
    return "".join(arr)


def check_request_sanity(values):
    if not 0 < values['port'] < 65536:
        return 'invalid port'
    if not values['left'] >= 0:
        return 'invalid amount remaining'
    if not values['downloaded'] >= 0:
        return 'invalid downloaded amount'
    if not values['uploaded'] >= 0:
        return 'invalid uploaded amount'
    if values['compact'] not in (0, 1):
        return 'compact must be 0 or 1'
    if not values['numwant'] >= 0:
        return 'invalid number of peers requested'
    if 'event' in values and values['event'] not in ('started', 'completed', 'stopped', 'update'):
        return 'invalid event'
    if values['peer_id'] is None:
        return 'peer id required'

    # all the data is good!
    return None


def parse_request(request):
    values = {}
    # request.encoding = 'iso-8859-1'

    parse_url = urlparse(request.url)
    query_dict = dict(parse_qsl(parse_url.query, encoding='latin_1'))

    # Get the interesting values from the request
    values['info_hash'] = to_hex(query_dict['info_hash'])
    values['peer_id'] = to_hex(query_dict['peer_id'])
    print("IPs -->", request.access_route, request.headers.getlist("X-Forwarded-For"))
    values['ip'] = request.environ['REMOTE_ADDR']  # ignore any sent ip address
    values['key'] = request.args.get('key', None)
    if request.args.get('event', None):  # Else Update
        values['event'] = request.args.get('event')

    # These are integer values and require special handling
    try:
        values['port'] = int(request.args.get('port', None))
        values['left'] = int(request.args.get('left', None))
        values['downloaded'] = int(request.args.get('downloaded', None))
        values['uploaded'] = int(request.args.get('uploaded', None))

        # Default values for parameters that arent required
        values['numwant'] = int(request.args.get('numwant', settings['numwant_default']))
        values['compact'] = int(request.args.get('compact', settings['compact_default']))
        values['no_peer_id'] = int(request.args.get('no_peer_id', settings['no_peer_id_default']))
    except ValueError:
        return None, 'error parsing integer field'
    except TypeError:
        return None, 'missing value for required field'

    return values, check_request_sanity(values)


def get_interval(peer):
    if peer.seeding:
        interval = settings['seed_interval']
    else:
        interval = settings['peer_interval']
    return interval


def tracker_error(value):
    return Response(bencode({'failure reason': "Error: %s" % value}), mimetype='text/plain')


def tracker_response(value):
    return Response(bencode(value), mimetype='text/plain')
