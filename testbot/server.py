import os

try:
    import json
except:
    import simplejson as json

from webenv.rest import RestApplication
from webenv import Response, HtmlResponse, Response201
from mako.lookup import TemplateLookup

this_directory = os.path.abspath(os.path.dirname(__file__))

lookup = TemplateLookup(directories=[os.path.join(this_directory, 'templates')], encoding_errors='ignore', input_encoding='utf-8', output_encoding='utf-8')

class MakoResponse(HtmlResponse):
    def __init__(self, name, **kwargs):
        template = lookup.get_template(name+'.mko')
        kwargs['json'] = json
        self.body = template.render_unicode(**kwargs).encode('utf-8', 'replace')
        self.headers = []
        
class JSONResponse(Response):
    content_type = 'application/json'
    def __init__(self, obj):
        self.body = json.dumps(obj)
        self.headers = []

class Response204(Response):
    status = '204 Not Content'

class TestBotApplication(RestApplication):
    def __init__(self, db, manager):
        RestApplication.__init__(self)
        self.db = db
        self.manager = manager
        self.add_resource("api", TestBotAPI(db, manager))
        
    def GET(self, request, collection=None, resource=None):
        if collection is None:
            return # Index
        if collection == 'clients':
            pass
        

class TestBotAPI(RestApplication):
    def __init__(self, db, manager):
        RestApplication.__init__(self)
        self.db = db
        self.manager = manager
        
    def POST(self, request, collection, resource=None):
        if collection == 'getJob':
            client_dict = json.loads(str(request.body))
            client = self.db.get(client_dict['_id'])
            if dict(client) != client_dict:
                client.update(client_dict)
                
            # Simplest job logic, pulls each jobtype by creation
            for jobtype in client['capabilities']['jobtypes']:
                result = self.db.views.jobs.pendingByJobtype(startkey=[jobtype, None],
                                                             endkey=[jobtype, {}],limit=1)
                if len(result) is 1:
                    job = result[0]
                    job.status = 'locked'
                    self.db.save(job)
                    return JSONResponse(job)
            return Response204()    
        
        if collection == 'newBuild':
            build = json.loads(str(request.body))
            build['type'] = 'build'
            info = self.db.create(build)
            build['_id'] = info['id']
            build['_rev'] = info['rev']
            jobs = self.manager.new_build(build)
            self.db.create(jobs)
            return JSONResponse(jobs)
        
        if collection == 'heartbeat':
            client = self.db.get(resource)
            status = json.loads(str(request.body))
            if client.get('status', None) != status:
                client.status = status
                info = self.db.save(client)
            return JSONResponse(info)
        
        if collection == 'report':
            job = self.db.get(resource)
            report = json.loads(str(request.body))
            # Add in support for report handlers
            return JSONResponse(report) # Debug response
        
    def GET(self, request, collection):
        if collection == 'whoami':
            name = request.query['name']
            assert name
            result = self.db.views.clients.byName(key=name)
            if len(result) is 0:
                info = self.db.create({"type":"client", "name":name})
                return JSONResponse(self.db.get(info['id']))
            else:
                return JSONResponse(result[0])



