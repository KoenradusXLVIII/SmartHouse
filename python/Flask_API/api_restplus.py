# Global imports
import yaml
from flask import Flask, jsonify, abort, make_response
from flask_restplus import Resource, Api
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

# Local imports
import hue

# Hue
with open('config.yaml', 'r') as fp:
    cfg = yaml.safe_load(fp)
hue_client = hue.Client(cfg['hue']['ip'])
hue_client.set_alarm_lights_by_name(cfg['hue']['alarm_lights'])

# Flask
app = Flask(__name__)
auth = HTTPBasicAuth()
api = Api(app, version='1.0', title='Hue API', description='A Flask API for Philips Hue')
ns = api.namespace('hue', description='Philips Hue')

users = {
    cfg['hue']['user']: generate_password_hash(cfg['hue']['pass'])
}


@auth.verify_password
def verify_password(username, password):
    if username in users:
        return check_password_hash(users.get(username), password)
    return False


@ns.route('/1.0/scene')
@auth.login_required
class AllScenes(Resource):
    def get(self):
        return {'all_off': hue_client.get_all_off(),
                'not_home': hue_client.check_scene_active(cfg['hue']['scenes']['not home']),
                'alarm': hue_client._alarm_active}


@auth.login_required
@ns.route('/1.0/scene/<string:name>')
class Scene(Resource):
    def post(self, name):
        if name == 'all_off':
            hue_client.set_all_off()
            return jsonify({'all_off': 'true'})
        elif name == 'not_home':
            hue_client.set_scene('Not home')
            return jsonify({'not_home': 'true'})
        else:
            abort(400)

'''
@app.route('/api/1.0/alarm', methods=['POST'])
@auth.login_required
def set_alarm():
    try:
        if request.json['enabled'] == 'true':
            hue_client.alarm(True)
            return jsonify({'enabled': 'true'})
        elif request.json['enabled'] == 'false':
            hue_client.alarm(False)
            return jsonify({'enabled': 'false'})
        else:
            abort(404)
    except (TypeError, KeyError):
        abort(400)
'''


if __name__ == '__main__':
    # app.run(host='0.0.0.0')
    app.run()