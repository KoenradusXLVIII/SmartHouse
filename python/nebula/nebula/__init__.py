import requests
import json

CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10

_nameToLevel = {
    'CRITICAL': CRITICAL,
    'ERROR': ERROR,
    'WARNING': WARNING,
    'INFO': INFO,
    'DEBUG': DEBUG,
}
_levelToName = {
    CRITICAL: 'CRITICAL',
    ERROR: 'ERROR',
    WARNING: 'WARNING',
    INFO: 'INFO',
    DEBUG: 'DEBUG',
}


class Client:
    def __init__(self, url, node_uuid, api_key):
        self.url = url
        self.auth = {'node_uuid': node_uuid, 'api_key': api_key, 'method': 'POST'}
        self.payload = []
        self.level = INFO

    def set_level(self, level):
        self.level = self._check_level(level)

    @staticmethod
    def _check_level(level):
        if isinstance(level, int):
            rv = level
        elif str(level) == level:
            if level not in _nameToLevel:
                raise ValueError("Unknown level: %r" % level)
            rv = _nameToLevel[level]
        else:
            raise TypeError("Level not an integer or a valid string: %r" % level)
        return rv

    def _trail(self, msg, level):
        url = self.url + '/api/graph/trail.php'
        data = self.auth.copy()
        data['level'] = _levelToName[level]
        data['message'] = json.dumps(msg)
        requests.post(url, json=data)

    def debug(self, msg):
        if DEBUG >= self.level:
            self._trail(msg, DEBUG)

    def info(self, msg):
        if INFO >= self.level:
            self._trail(msg, INFO)

    def warning(self, msg):
        if WARNING >= self.level:
            self._trail(msg, WARNING)

    def error(self, msg):
        if ERROR >= self.level:
            self._trail(msg, ERROR)

    def critical(self, msg):
        if CRITICAL >= self.level:
            self._trail(msg, CRITICAL)

    def add_single(self, sensor_id, value):
        self.payload.append({'sensor_id': sensor_id, 'value': '%.2f' % float(value)})

    def post_single(self, sensor_id, value):
        self.add_single(sensor_id, value)
        r = self.post()
        return r

    def add_many(self, payload):
        for sensor_id, value in payload.items():
            self.add_single(sensor_id, value)

    def post_many(self, payload):
        self.add_many(payload)
        r = self.post()
        return r

    def post(self):
        url = self.url + '/api/graph/post.php'
        data = self.auth.copy()
        data['values'] = self.payload
        r = requests.post(url, json=data)
        self.clear()
        return r

    def clear(self):
        self.payload = []

