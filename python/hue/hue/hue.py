from phue import Bridge


class Client:
    def __init__(self, ip):
        self.ip = ip
        self.bridge = Bridge(self.ip)
        self.lights = self.bridge.lights
        self.scenes = self.bridge.scenes
        self.groups = self.bridge.groups

    def get_ip(self):
        return self.ip

    def get_scene(self, scene):
        for id in scene['lights']:
            if scene['lights'][id]['state']:
                # Light should be on, verify that it is
                if self.lights[id].on:
                    # Light is on, verify xy brightness and color (xy)
                    if not scene['lights'][id]['brightness'] == self.lights[id].brightness or \
                            not self.compare_xy(scene['lights'][id]['xy'], self.lights[id].xy, scene['xy_tolerance']):
                        return False
                else:
                    return False
            else:
                # Light should be off, verify that it is
                if self.lights[id].on:
                    return False

        return True

    def compare_xy(self, xy_scene, xy_lights, xy_tolerance):
        if (xy_lights[0] > (xy_scene[0] - xy_tolerance)) and (xy_lights[0] < (xy_scene[0] + xy_tolerance)):
            if (xy_lights[1] > (xy_scene[1] - xy_tolerance)) and (xy_lights[1] < (xy_scene[1] + xy_tolerance)):
                return True

        return False


    def get_scene_id_by_name(self, name):
        for scene in self.scenes:
            if scene.name == name:
                return scene.scene_id

    def set_scene(self, name):
        self.bridge.activate_scene(self.groups[0].group_id, self.get_scene_id_by_name(name))

    def get_all_off(self):
        for light in self.lights:
            if light.on:
                return False

        return True

    def set_all_off(self):
        self.groups[0].on = False
