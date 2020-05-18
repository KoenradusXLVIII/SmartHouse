# Global imports
import os
import yaml
from flask import Flask, jsonify, abort, flash, request, redirect, url_for, send_from_directory, make_response
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Local imports
import hue


# Load configuration
with open('config.yaml', 'r') as fp:
    cfg = yaml.safe_load(fp)

# Hue
hue_client = hue.Client(cfg['hue']['ip'])
hue_client.set_alarm_lights_by_name(cfg['hue']['alarm_lights'])

# Flask
users = {cfg['flask']['user']: generate_password_hash(cfg['flask']['pass'])}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = cfg['upload']['folder'] 
app.config['MAX_CONTENT_LENGTH'] = cfg['upload']['max_content_length']
auth = HTTPBasicAuth()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in cfg['upload']['allowed_extensions']
           

@auth.verify_password
def verify_password(username, password):
    if username in users:
        return check_password_hash(users.get(username), password)
    return False
    
    
@app.route('/', methods=['GET'])
def home():
    return '' 
    
    
@app.route('/upload/', methods=['POST'])
@auth.login_required
def upload_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        abort(400)
        return redirect(request.url)
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        abort(400)
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return jsonify({'upload':filename})
         
    
@app.route('/api/', methods=['GET'])    
@app.route('/api/1.0', methods=['GET'])
@auth.login_required
def api():
    return '' 


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


@app.errorhandler(405)
def not_found(error):
    return make_response(jsonify({'error': 'method not allowed'}), 405)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'not found'}), 404)


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'bad request'}), 400)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
