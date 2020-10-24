# Global imports
import os
import yaml
import time
import paho.mqtt.client as mqtt
import requests

# Load secure configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
fp = open(path + '/config.yaml', 'r')
cfg = yaml.load(fp, Loader=yaml.FullLoader)

# Local configuration
day_night_value = 0 # Default to day = light off
day_night_topic = 'nodes/90A2DA0EC568/sensors/20'
front_door_light_value = 0 # Default to day = light off
front_door_light_topic = 'nodes/joost/app/io/front_door_light'
payload = {'deviceid': cfg['sonoff']['deviceid'], 'data': {'switch': 'off'}}

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global day_night_value
    global front_door_light_value
    global payload

    val = int(msg.payload.decode('UTF-8'))
    print('%s => %d [retained: %s]' % (msg.topic, val, bool(msg.retain)))
    if msg.topic == day_night_topic:
        day_night_value = val
    elif msg.topic == front_door_light_topic:
        front_door_light_value = val
        if front_door_light_value:
            payload['data']['switch'] = 'on'
        else:
            payload['data']['switch'] = 'off'
        requests.post('%s:%d/%s' % (cfg['sonoff']['host'], cfg['sonoff']['port'], cfg['sonoff']['switch']), json=payload, timeout=1)

# Main function
def main():
    # Set up MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.username_pw_set(username=cfg['mqtt']['username'], password=cfg['mqtt']['password'])
    mqtt_client.connect(cfg['mqtt']['host'], cfg['mqtt']['port'])
    mqtt_client.subscribe(day_night_topic)
    mqtt_client.subscribe(front_door_light_topic)

    # Get day/night state
    mqtt_client.loop_start()
    time.sleep(1)
    mqtt_client.loop_stop()

    # Check if day/night change occurred:
    if day_night_value: # It is night
        if not front_door_light_value: # But the light is off
            # Turn it on
            mqtt_client.publish(front_door_light_topic, 1, retain=True)
    else: # It is day
        if front_door_light_value: # And the light is on
            # Turn it off
            mqtt_client.publish(front_door_light_topic, 0, retain=True)

    # Publish any changes
    mqtt_client.loop_start()
    time.sleep(1)
    mqtt_client.loop_stop()


if __name__ == '__main__':
    main()
