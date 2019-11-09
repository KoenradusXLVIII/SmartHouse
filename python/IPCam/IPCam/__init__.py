import requests
import time
import re
import os
from xml.etree import ElementTree


# noinspection SpellCheckingInspection,SpellCheckingInspection
class Client:
    def __init__(self, ip, port, usr, pwd, name):
        self.url = 'http://' + ip + ':' + port + '/'
        # noinspection SpellCheckingInspection
        self.CGI = self.url + 'cgi-bin/CGIProxy.fcgi'
        self.usr = usr                  # Foscam user needs admin rights to access getDevState!
        self.pwd = pwd
        self.name = name
        self.timeout = 1                # seconds
        self.connection_timeout = 60     # seconds

        # Internal variables
        self._last_connection_time = 0
        self._last_day_night_state = None
        self._data = None
        self._path = ''
        self._no_files = 0

        # Try to connect to the device
        self._check_connection()

    def _check_connection(self):
        payload = {'usr': self.usr, 'pwd': self.pwd, 'cmd': 'getDevInfo'}
        try:
            r = requests.get(self.CGI, params=payload, timeout=self.timeout)
            if r.status_code == requests.codes.ok:
                data = ElementTree.fromstring(r.text)  # Extract XML tree
                if data.find('result').text == '0':
                    return True
                else:
                    raise ConnectionError('Unable to login')
            else:
                raise ConnectionError('Invalid response')
        except requests.exceptions.Timeout:
            raise ConnectionError('Connection timeout')

    def _get_devstate(self):
        if (time.time() - self._last_connection_time) > self.connection_timeout:
            payload = {'usr': self.usr, 'pwd': self.pwd, 'cmd': 'getDevState'}
            try:
                r = requests.get(self.CGI, params=payload, timeout=self.timeout)
                self._data = ElementTree.fromstring(r.text)  # Extract XML tree
                self._last_connection_time = time.time()
            except requests.exceptions.Timeout:
                self._data = None
            except ElementTree.ParseError:
                self._data = None

    def set_base_path(self, base_path):
        self._path = os.path.join(base_path, self.name)
        self._path = os.path.join(self._path, 'record')
        self._no_files = self._count_recordings()

    def new_recording(self):
        new_recording = False
        if self._path:
            no_files = self._count_recordings()
            if no_files > self._no_files:
                # New recording detected
                new_recording = True

            self._no_files = no_files
            return new_recording
        else:
            raise Exception('Recording base path not set!')

    def _count_recordings(self):
        files = [f for f in os.listdir(self._path) if f.endswith('.mkv')]
        return len(files)

    def motion_detect(self):
        self._get_devstate()
        if self._data is not None:
            if self._data.find('motionDetectAlarm').text == '1':
                # No motion detected
                return False
            elif self._data.find('motionDetectAlarm').text == '2':
                # Motion detected
                return True

        # Unknown state
        return None

    def delta_day_night(self):
        self._get_devstate()
        day_night_state = int(self._data.find('infraLedState').text)

        # Only report changes
        if  day_night_state != self._last_day_night_state:
            self._last_day_night_state = day_night_state
            return day_night_state
        else:
            return None

    def snapshot(self):
        payload = {'usr': self.usr, 'pwd': self.pwd, 'cmd': 'snapPicture'}
        try:
            r = requests.get(self.CGI, params=payload, timeout=self.timeout)
            reg = re.search(r'(Snap_\d{8}-\d{6}.jpg)', r.text)  # Get snapshot name: Snap_YYYYMMDD_HHMMSS.jpg
            r = requests.get(self.url + 'snapPic/' + reg.group(1))
            return r.content
        except requests.exceptions.Timeout:
            return None




