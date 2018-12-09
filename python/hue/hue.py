import yaml
import time
import random
import logger
from phue import Bridge

# Load configuration YAML
fp = open('config.yaml','r')
cfg = yaml.load(fp)

# Set up logger client
log_client = logger.Client('foscam', log_level='info')


def main():
    # Connect to Hue Bridge
    b = Bridge(cfg['hue']['url'])
    # Get current light state
    hueLights = b.lights
    hueGroups = b.groups
    hueScenes = b.scenes

    # Check if all lights off
    all_off = True
    for light in hueLights:
        if not light.on:
            all_off = False
    if all_off:
        b.activate_scene(hueGroups[0].group_id, get_scene_by_name('Away', hueScenes))

    # Check if 'away' scene active
    if get_active_scene('away', hueLights):
        # Turn all lights off within a set random time
        time.sleep(random.randint(1,cfg['hue']['random']))
        log_client.info('Lights out!')
        hueGroups[0].on = False


def get_active_scene(name, lights):
    for id in cfg['hue']['scenes'][name]['lights']:
        if cfg['hue']['scenes'][name]['lights'][id]['state']:
            # Light should be on, verify that it is
            if (lights[id].on):
                # Light is on, verify xy brightness and color (xy)
                if not cfg['hue']['scenes'][name]['lights'][id]['brightness'] == lights[id].brightness or \
                        not cfg['hue']['scenes'][name]['lights'][id]['xy'] == lights[id].xy:
                    return False
            else:
                return False
        else:
            # Light should be off, verify that it is
            if lights[id].on:
                return False
    return True


def get_scene_by_name(name, scenes):
    for scene in scenes:
        if scene.name == name:
            return scene.scene_id
    return 0

if __name__ == "__main__":
    main()


