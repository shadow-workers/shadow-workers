import os
import yaml
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from database.models import metadata
from flask_migrate import Migrate
from flask_httpauth import HTTPBasicAuth

db = SQLAlchemy(metadata = metadata)
auth = HTTPBasicAuth()

extraModules = []
files = os.listdir('app/templates/modules')
for name in files:
    if name != 'template.js':
        extraModules.append(name.replace('.js', ''))
extraModules = {'modules':extraModules}

global ConnectedAgents
ConnectedAgents = {}
global ConnectedDomAgents
ConnectedDomAgents = {}

global AutomaticModuleExecution
AutomaticModuleExecution = []

@auth.verify_password
def verify_pw(username, password):
    if username == Config.USERNAME and password == Config.PASSWORD:
        return True
    return False
    
# this has to come after, otherwise cannot access db from controllers
from app.dashboard.controllers import dashboard
from app.modules.controllers import modules
from app.agent.controllers import agent

def define_routes(app):
    app.register_blueprint(dashboard, url_prefix = '/dashboard')
    app.register_blueprint(modules, url_prefix = '/modules')
    app.register_blueprint(agent, url_prefix = '/agent/<token>')
    return

def create_app():
    app = Flask("C2", static_folder="app/static", template_folder="app/templates")
    app.config.from_object(Config)
    app.app_context().push()
    db.init_app(app)
    migrate = Migrate(app, db)
    define_routes(app)
    return app
