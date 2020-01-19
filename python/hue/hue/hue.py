from phue import Bridge


class Client:
    def __init__(self, ip):
        self.ip = ip
        self.bridge = Bridge(self.ip)
        self.lights = self.bridge.lights
        self.scenes = self.bridge.scenes
        self.groups = self.bridge.groups

        # Internal variables
        self._last_lights = []
        self._alarm_lights = []
        self._alarm_lights_state = []
        self._alarm_active = False

    def check_scene_active(self, scene):
        for id in scene['lights']:
            if scene['lights'][id]['state']:
                # Light should be on, verify that it is
                if self.lights[id].on:
                    # Light is on, verify xy brightness and color (xy)
                    if not scene['lights'][id]['brightness'] == self.lights[id].brightness or \
                            not self._compare_xy(scene['lights'][id]['xy'], self.lights[id].xy, scene['xy_tolerance']):
                        return False
                else:
                    return False
            else:
                # Light should be off, verify that it is
                if self.lights[id].on:
                    return False
        return True

    def set_scene(self, name):
        if name == 'All off':
            self.set_all_off()
        elif name == 'Not home':
            self.bridge.activate_scene(self._get_group_id_by_name('Woonkamer'), self._get_scene_id_by_name(name))

    def get_light_changes(self):
        lights = []
        for light in self.lights:
            lights.append(self._get_light_state(light))

        if lights != self._last_lights:
            self._last_lights = lights
            return self._last_lights

    def set_all_off(self):
        for group in self.groups:
            group.on = False

    def get_all_off(self):
        for light in self.lights:
            if light.on:
                return False
        return True

    def set_alarm_lights_by_name(self, names):
        self._alarm_lights = []
        if not isinstance(names, list):
            names = [names]
        for name in names:
            for light in self.lights:
                if light.name == name:
                    self._alarm_lights.append(light)

    def alarm(self, active):
        if active:
            if not self._alarm_active:
                # Store current light state
                for light in self._alarm_lights:
                    self._alarm_lights_state.append(self._get_light_state(light))

            for light in self._alarm_lights:
                if light.on:
                    # Light is on, turn it off
                    light.on = False
                else:
                    # Light is off, change to red, and on
                    light.on = True
                    light.xy = [0.6708, 0.3205]
                    light.brightness = 254
        else:
            if self._alarm_active:
                # Alarm disabled, return to previous light state
                for itt, light in enumerate(self._alarm_lights):
                    if self._alarm_lights_state[itt]['brightness'] > 0:
                        # The light was originally on
                        light.on = True
                        light.brightness = self._alarm_lights_state[itt]['brightness']
                        light.xy = self._alarm_lights_state[itt]['xy']
                    else:
                        # The light was originally on
                        light.on = False

        self._alarm_active = active

    def _get_light_state(self, light):
        if light.on:
            return {'id': light.light_id, 'brightness': light.brightness, 'xy': light.xy}
        else:
            return {'id': light.light_id, 'brightness': 0, 'xy': ''}

    def _get_scene_id_by_name(self, name):
        for scene in self.scenes:
            if scene.name == name:
                return scene.scene_id

    def _get_group_id_by_name(self, name):
        for group in self.groups:
            if group.name == name:
                return group.group_id

    def _compare_xy(self, xy_scene, xy_lights, xy_tolerance):
        if (xy_lights[0] > (xy_scene[0] - xy_tolerance)) and (xy_lights[0] < (xy_scene[0] + xy_tolerance)):
            if (xy_lights[1] > (xy_scene[1] - xy_tolerance)) and (xy_lights[1] < (xy_scene[1] + xy_tolerance)):
                return True

        return False
