import time
from datetime import datetime
from app import db, ConnectedAgents, auth, extraModules, AutomaticModuleExecution
from flask import jsonify, send_from_directory, Blueprint, Response, render_template
from pywebpush import webpush, WebPushException
from database.models import Registration, Agent, Module
from sqlalchemy.orm import joinedload

dashboard = Blueprint('dashboard', __name__)

AGENT_TIMEOUT = 8

@dashboard.after_request
def apply_csp(response):
    response.headers["Content-Security-Policy"] = "script-src 'self'; style-src 'self'; img-src 'self'; font-src 'self'; media-src 'self'; frame-src 'self'; frame-ancestors 'none'"
    return response

@dashboard.route('/')
@auth.login_required
def servedashboard():
    return render_template('index.html')

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
            modules = db.session().query(Module).filter(Module.agentId == agentID, Module.processed == 1).all()
            if len(modules) != 0:
                result['modules'] = {}
                for module in modules:
                    result['modules'][module.name] = module.results
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

def activeAgents():
    now = time.time()
    agentsToRemove = {}
    for agentID in ConnectedAgents:
        if (now - ConnectedAgents[agentID]['last_seen']) > AGENT_TIMEOUT:
            agentsToRemove[agentID] = ConnectedAgents[agentID]
    for agentID in agentsToRemove:
        del ConnectedAgents[agentID]

def dormantAgents():
    agents = db.session().query(Agent).options(joinedload('registration')).filter(Agent.id.notin_(ConnectedAgents.keys())).all()
    results = {}
    for agent in agents:
        results[agent.id] = Agent.to_json(agent)
        results[agent.id]['push'] = str(agent.registration is not None).lower()
        results[agent.id]['active'] = 'false'
    return results

def loadAgentModule(moduleName, agentID):
    checkModule(moduleName)
    return db.session.query(Module).filter(Module.agentId == agentID, Module.name == moduleName).order_by(Module.id.desc()).first()
    
def checkModule(moduleName):
    if moduleName not in extraModules['modules']:
        return Response("", 404)