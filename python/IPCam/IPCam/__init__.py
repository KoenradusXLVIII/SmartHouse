import requests
import time
import re
from xml.etree import ElementTree

class Client:
    def __init__(self, ip, port, usr, pwd):
        self.url = 'http://' + ip + ':' + port + '/'
        self.CGI = self.url + 'cgi-bin/CGIProxy.fcgi'
        self.usr = usr # Foscam user needs admin rights to access getDevState!
        self.pwd = pwd
        self.timeout = 1 # seconds
        self.motion_hysteresis = 30  # seconds

        # Internal variables
        self._last_motion_state = False
        self._last_motion_time = 0
        self._last_day_night_state = 0


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
        payload = {'usr': self.usr, 'pwd': self.pwd, 'cmd': 'getDevState'}
        try:
            r = requests.get(self.CGI, params=payload, timeout=self.timeout)
            return ElementTree.fromstring(r.text)  # Extract XML tree
        except requests.exceptions.Timeout:
            return None
        except ElementTree.ParseError:
            return None

    def motion_detect(self):
        data = self._get_devstate()
        if data.find('motionDetectAlarm').text == '1':
            self.last_motion_state = False
            return False
        elif data.find('motionDetectAlarm').text == '2':
            # Motion detected
            if not self.last_motion_state:
                # New motion detected
                self.last_motion_state = True
                if self.motion_timeout():
                    # New motion detected outside hysteresis window
                    self._last_motion_time = time.time()
                    return True
                else:
                    # New motion detected inside hysteresis window, reset time
                    self._last_motion_time = time.time()
                    print('Reset')
                    return False
            else:
                # Only report new motions
                return False
        else:
            # Unknown state
            return None

    def motion_timeout(self):
        return (time.time() - self._last_motion_time) > self.motion_hysteresis

    def day_night(self):
        data = self._get_devstate()
        try:
            day_night_state = int(data.find('infraLedState').text)
        except (AttributeError, ValueError):
            return None

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
            r = requests.get(self.url+ 'snapPic/' + reg.group(1))
            return r.content
        except requests.exceptions.Timeout:
            return None




