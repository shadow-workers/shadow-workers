import os
basedir = os.path.abspath(os.path.dirname(__file__))
password_file = open('./.password', 'r')
agenttoken_file = open('./.agenttoken', 'r')

class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'http.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    USERNAME = 'workers'
    PASSWORD = password_file.read().strip() or 'easypeasy'
    AGENT_TOKEN = agenttoken_file.read().strip() or 'seriousbusiness'
    HOST = os.environ['HOST'] if 'HOST' in os.environ else '127.0.0.1'
    PORT = os.environ['PORT'] if 'PORT' in os.environ else 5000
    HTTPS = True if 'SW_HTTPS' in os.environ else False
    SSL_CERT = os.environ['SW_CERT'] if 'SW_CERT' in os.environ else 'cert.pem'
    SSL_KEY = os.environ['SW_KEY'] if 'SW_KEY' in os.environ else 'key.pem'
