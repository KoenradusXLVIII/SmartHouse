def get_active_scene(name, lights, cfg):
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