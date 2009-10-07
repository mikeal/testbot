import sys

try:
    import json
except:
    import simplejson as json

from wsgiref.simple_server import make_server
from couchquery import Database
from webenv.rest import RestApplication
from webenv import Response200


class TestBotApplication(RestApplication):
    def __init__(self, db):
        RestApplication.__init__(self)
        self.db = db
        self.add_resource("api", TestBotAPI(db))

class TestBotAPI(RestApplication):
    def __init__(self, db):
        RestApplication.__init__(self)
        self.db = db
    def POST(self, request, collection, resource=None):
        if collection == 'getJob':
            client_dict = json.loads(str(request.body))
            client = self.db.get(client_dict['_id'])
            if dict(client) != client_dict:
                client.update(client_dict)
                
            # Add job getting logic
            
        
        if collection == 'heartbeat':
            client = self.db.get(resource)
            status = json.loads(str(request.body))
            if client.status != status:
                client.status = status
                self.db.save(client)
            return Response200('')
        
        
    def GET(self, request, collection):
        if collection == 'whoami':
            print dir(request.query)
            result = self.db.views.clients.clientByName(key=name)

def cli():
    if not sys.argv[-1].startswith('http'):
        dburi = 'http://localhost:5984/testbot'
    else:
        dburi = sys.argv[-1]
    
    db = Database(dburi)
    print "Using CouchDB @ "+dburi
    application = TestBotApplication(db)
    httpd = make_server('', 8888, application)
    print "Serving on http://localhost:8888/"
    httpd.serve_forever()

