# Public imports
import time
import uuid
import paho.mqtt.client as mqtt


class Client:
    def __init__(self, **cfg):
        # Local variables
        self._username = cfg['username']
        self._password = cfg['password']
        self._host = cfg['host']
        self._port = cfg['port']
        #self._mac = ''.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0, 8 * 6, 8)][::-1]).upper()
        self._retained_msgs = []
        self._topics = []
        self._nodes = []
        self._mqtt_connected = False

        # Initialise MQTT object
        self._mqtt_client = mqtt.Client()
        self._mqtt_client.username_pw_set(username=self._username, password=self._password)
        self._mqtt_client.on_message = self._on_message

    def _on_message(self, client, userdata, msg):
        # The callback for when a PUBLISH message is received from the server.
        if msg.retain:
            self._retained_msgs.append(msg)

    def _decode_msg(self, msg, msgs, filter, type):
        _, mac, sensor_id = msg.topic.split('/')
        value = msg.payload.decode('UTF-8')
        #print('Decoding message | sensor_id: %s, value: %s' % (sensor_id, value))
        if len(filter):
            if not sensor_id in filter:
                return

        # Cast to correct type
        if type == 'int':
            msgs[sensor_id] = int(value)
        elif type == 'float':
            msgs[sensor_id] = float(value)
        elif type == 'str':
            msgs[sensor_id] = str(value)

    def subscribe(self, topic):
        self._topics.append(topic)

    def get_single(self, filter, type='int'):
        msg = self.get(filter, type)
        return list(msg.values())[0]

    def get(self, filter=[], type='int'):
        msgs = {}
        if not isinstance(filter, list):
            filter = [str(filter)]
        else:
            for itt, val in enumerate(filter):
                filter[itt] = str(val)

        #print('Active filter: %s' % filter)

        self._mqtt_client.connect(self._host)
        for topic in self._topics:
            self._mqtt_client.subscribe(topic)
        self._mqtt_client.loop_start()
        time.sleep(1)
        self._mqtt_client.loop_stop()
        self._mqtt_client.disconnect()

        # Process messages
        for msg in self._retained_msgs:
            self._decode_msg(msg, msgs, filter, type)

        print(msgs)
        return msgs

    def set_mac(self, mac):
        self._mac = mac

    def publish(self, node, sensor_id, value):
        topic = 'nodes/%s/%s' % (node, sensor_id)
        self._mqtt_client.connect(self._host)
        self._mqtt_client.publish(topic, value, retain=True)
        self._mqtt_client.disconnect()
        print(topic, value)
