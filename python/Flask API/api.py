# Global imports
import yaml
from flask import Flask, jsonify, request, abort, make_response
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

# Local imports
import hue

# Flask
app = Flask(__name__)
auth = HTTPBasicAuth()

users = {
    "hue": generate_password_hash('crD8DtCID83bF*X*v&OyGjanbV339Bxs')
}


@auth.verify_password
def verify_password(username, password):
    if username in users:
        return check_password_hash(users.get(username), password)
    return False


@app.route('/api/1.0/scene', methods=['GET'])
@auth.login_required
def get_scenes():
    return jsonify({'all_off': hue_client.get_all_off(),
                    'not_home': hue_client.check_scene_active(cfg['hue']['scenes']['not home']),
                    'alarm': hue_client._alarm_active})


@app.route('/api/1.0/scene', methods=['POST'])
@auth.login_required
def set_scene():
    try:
        if request.json['scene'] == 'all_off':
            hue_client.set_all_off()
            return jsonify({'all_off': 'true'})
        elif request.json['scene'] == 'not_home':
            hue_client.set_scene('Not home')
            return jsonify({'not_home': 'true'})
        else:
            abort(404)
    except (TypeError, KeyError):
        abort(400)


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


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'not found'}), 404)


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'bad request'}), 404)


# Hue
with open('config.yaml', 'r') as fp:
    cfg = yaml.safe_load(fp)
hue_client = hue.Client(cfg['hue']['ip'])
hue_client.set_alarm_lights_by_name(cfg['hue']['alarm_lights'])


if __name__ == '__main__':
    app.run(debug=True)
    # app.run(ssl_context='adhoc')
