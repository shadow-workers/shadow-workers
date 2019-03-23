from sqlalchemy import MetaData, Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

metadata = MetaData()
Base = declarative_base(metadata=metadata)

class Registration(Base):
    __tablename__ = 'registrations'
    agent = relationship("Agent", back_populates="registration")

    id = Column(Integer, primary_key=True)
    endpoint = Column(Text, nullable=False)
    authKey = Column(Text, nullable=False)
    authSecret = Column(Text, nullable=False)
    agentId = Column(Text, ForeignKey('agents.id'), nullable=False, index=True)
    
    def __init__(self, id, endpoint, authKey, authSecret, agentId):
        self.id = id
        self.endpoint = endpoint
        self.authKey = authKey
        self.authSecret = authSecret
        self.agentId = agentId

class Url(Base):
    __tablename__ = 'urls'
    agent = relationship("Agent", back_populates="urls")

    id = Column(String(156), primary_key=True)
    url = Column(Text, nullable=False)
    request = Column(Text)
    response = Column(Text)
    processed = Column(Integer, nullable=False)
    agentId = Column(Text, ForeignKey('agents.id'), nullable=False, index=True)
    time_stamp = Column(TIMESTAMP)

    def __init__(self, id, url, request, response, processed, agentId, time_stamp):
        self.id = id
        self.url = url
        self.request = request
        self.response = response
        self.processed = processed
        self.agentId = agentId
        self.time_stamp = time_stamp

class Agent(Base):
    __tablename__ = 'agents'
    registration = relationship("Registration", back_populates="agent", cascade="all, delete-orphan")
    modules = relationship("Module", cascade="all, delete-orphan")
    urls = relationship("Url", cascade="all, delete-orphan")
    dom_commands = relationship("DomCommand", cascade="all, delete-orphan")
    
    id = Column(String(156), primary_key=True)
    first_seen = Column(TIMESTAMP, nullable=False)
    last_seen = Column(TIMESTAMP, nullable=False)
    domain = Column(Text, nullable=False)
    port = Column(Text, nullable=False)
    ip = Column(Text, nullable=False)
    user_agent = Column(Text, nullable=True)
    
    def __init__(self, id, first_seen, last_seen, domain, port, ip, user_agent):
        self.id = id
        self.first_seen = first_seen
        self.last_seen = last_seen
        self.domain = domain
        self.port = port
        self.ip = ip
        self.user_agent = user_agent
        
    def to_json(agent):
        return {'id': agent.id, 'first_seen': agent.first_seen, 'last_seen': agent.last_seen, 'domain': agent.domain, 'port': agent.port, 'ip': agent.ip}

class Module(Base):
    __tablename__ = 'modules'
    agent = relationship("Agent", back_populates="modules")

    id = Column(Integer, primary_key=True)
    agentId = Column(Text, ForeignKey('agents.id'), nullable=False, index=True)
    name = Column(Text, nullable=False)
    results = Column(Text)
    processed = Column(Integer, nullable=False)
    lastUpdated = Column(TIMESTAMP)

    def __init__(self, id, agentId, name, results, processed, lastUpdated):
        self.id = id
        self.agentId = agentId
        self.name = name
        self.results = results
        self.processed = processed
        self.lastUpdated = lastUpdated

class DomCommand(Base):
    __tablename__ = 'dom_commands'
    agent = relationship("Agent", back_populates="dom_commands")

    id = Column(Integer, primary_key=True)
    agentId = Column(Text, ForeignKey('agents.id'), nullable=False, index=True)
    command = Column(Text)
    result = Column(Text)
    processed = Column(Integer, nullable=False)
    lastUpdated = Column(TIMESTAMP)

    def __init__(self, id, agentId, command, result, processed, lastUpdated):
        self.id = id
        self.agentId = agentId
        self.command = command
        self.result = result
        self.processed = processed
        self.lastUpdated = lastUpdated

class DashboardRegistration(Base):
    __tablename__ = 'dashboard_registrations'

    id = Column(Integer, primary_key=True)
    endpoint = Column(Text, nullable=False)
    authKey = Column(Text, nullable=False)
    authSecret = Column(Text, nullable=False)
    
    def __init__(self, id, endpoint, authKey, authSecret):
        self.id = id
        self.endpoint = endpoint
        self.authKey = authKey
        self.authSecret = authSecret
