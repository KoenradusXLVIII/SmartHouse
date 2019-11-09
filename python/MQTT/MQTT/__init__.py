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

        # Local objects
        self._mqtt_client = mqtt.Client()

        # Execution
        self._connect()

    def _connect(self):
        self._mqtt_client.username_pw_set(username=self._username, password=self._password)
        self._mqtt_client.connect(self._host)
        self._mqtt_client.on_message = self._on_message

    def _on_message(self, client, userdata, msg):
        # The callback for when a PUBLISH message is received from the server.
        if msg.retain:
            self._retained_msgs.append(msg)

    def _decode_msg(self, msg, msgs, filter):
        _, mac, sensor_id = msg.topic.split('/')
        value = msg.payload.decode('UTF-8')
        #print('Decoding message | sensor_id: %s, value: %s' % (sensor_id, value))
        if len(filter):
            if sensor_id in filter:
                msgs[sensor_id] = value
        else:
            msgs[sensor_id] = value

    def subscribe(self, topic):
        self._topics.append(topic)
        self._mqtt_client.subscribe(topic)

    def get_single(self, filter):
        msg = self.get(filter)
        return list(msg.values())[0]

    def get(self, filter=[]):
        msgs = {}
        if not isinstance(filter, list):
            filter = [str(filter)]
        else:
            for itt, val in enumerate(filter):
                filter[itt] = str(val)

        #print('Active filter: %s' % filter)

        # Proces MQTT queue
        self._mqtt_client.loop_start()
        time.sleep(.1)
        self._mqtt_client.loop_stop()

        # Process messages
        for msg in self._retained_msgs:
            self._decode_msg(msg, msgs, filter)

        print(msgs)
        return msgs

    def set_mac(self, mac):
        self._mac = mac

    def publish(self, node, sensor_id, value):
        topic = 'nodes/%s/%s' % (node, sensor_id)
        print(topic, value)
        self._mqtt_client.publish(topic, value, retain=True)
