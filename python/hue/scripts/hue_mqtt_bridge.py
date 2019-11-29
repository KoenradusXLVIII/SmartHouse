# Public imports
import os
import yaml
import time
import paho.mqtt.client as mqtt

# Private imports
import hue

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
fp = open(path + '/config.yaml', 'r')
cfg = yaml.load(fp)

# Set up Hue client
hue_client = hue.Client(cfg['hue']['ip'])

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    if not msg.retain:
        msg.payload = msg.payload.decode('UTF-8')
        print('%s => %s' % (msg.topic, msg.payload))
        if 'scene' in msg.topic:
            hue_client.set_scene(msg.payload)

# Main function
def main():
    # Set up MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.username_pw_set(username=cfg['mqtt']['username'], password=cfg['mqtt']['password'])
    mqtt_client.connect(cfg['mqtt']['host'], cfg['mqtt']['port'])
    mqtt_client.subscribe("hue/#")
    last_published_scene = ''

    # Set up timer (force refresh on boot)
    start_time = time.time() - cfg['hue']['refresh_rate']

    while True:
        mqtt_client.loop()
        if time.time() - start_time > cfg['hue']['refresh_rate']:
            start_time = time.time()
            lights = hue_client.get_light_changes()
            if lights:
                for light in lights:
                    mqtt_client.publish('hue/lights/brightness/%d' % light['id'], light['brightness'], retain=True)
                    mqtt_client.publish('hue/lights/xy/%d' % light['id'], str(light['xy']), retain=True)
            if hue_client.get_all_off():
                mqtt_client.publish('hue/scene', 'All off', retain=True)
            elif hue_client.check_scene_active(cfg['hue']['scenes']['not home']):
                if last_published_scene is not 'Not home':
                    last_published_scene = 'Not home'
                    mqtt_client.publish('hue/scene', 'Not home', retain=True)
            else:
                if last_published_scene is not 'Home':
                    last_published_scene = 'Home'
                    mqtt_client.publish('hue/scene', 'Home', retain=True)


if __name__ == '__main__':
    main()



