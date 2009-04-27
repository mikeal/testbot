import os
import copy
try:
    import json
except:
    import simplejson as json

from webenv import Response, Response404, Response500, Response201
from webenv.rest import RestApplication

_default_store = {'resources':{}, 'types':{}, 'pools':{}}

class FileStorage(object):
    def __init__(self, filename='~/.testbotmaster.json'):
        self.filename = os.path.abspath(os.path.expanduser(filename))
        if os.path.isfile(self.filename):
            f = open(self.filename, 'r')
            self.storage = json.loads(f.read())
            f.close()
        else:
            self.store = copy.copy(_default_store)
    
    def save(self):
        f = open(self.filename, 'w')
        f.write(json.dumps(self.store))
        f.close()
        
    def get_resource(self, rid):
        return self.store['resources'][rid]
    # def get_type(self, rtype):
    #     return self.store['types'][rtype]
    def get_pool(self, poolid):
        return self.store['pools'][poolid]
    
    # def get_all_types(self):
    #     return self.store['types']
    def get_all_resources(self):
        return self.store['resources']
    def get_all_pools(self):
        return self.store['pools']
        
    def lock_resource(self, rid):
        self.store['resources'][rid]['locked'] = True
        for p in self.store.pools.values():
            if rid in p['resources']:
                p['resources'][rid]['locked'] = True
        self.save()
    
    def unlock_resource(self, rid):
        self.store['resources'][rid]['locked'] = False
        for p in self.store.pools.values():
            if rid in p['resources']:
                p['resources'][rid]['locked'] = False
        self.save()
    
    def add_resource(self, obj):
        r = obj['resource_id']
        self.store['resources'][r] = obj
        self.save()
        
    def add_resource_to_pool(self, poolid, rid):
        r = self.storage['resources'][rid]
        self.storage['pools'][poolid].setdefault('resources', {})[rid] = r
        r.setdefault('pools', {})[poolid] = self.storage['pools'][poolid]
        self.save()
        
    def add_pool(self, obj):
        r = obj['pool_id']
        self.store['pools'][r] = obj
        self.save()
        
    # def add_type(self, obj):
    #     r = obj['type_id']
    #     self.store['types'][r] = obj
    #     self.save()

class JSONResponse(Response):
    content_type = "application/json"
    def __init__(self, obj):
        self.headers = []
        self.body = json.dumps(obj)

class MasterRestApplication(RestApplication):
    def __init__(self, storage):
        self.storage = storage
        super(MasterRestApplication, self).__init__()
        
    def POST(self, request, query_type):
        # if query_type == "types":
        #     self.storage.add_type(json.loads(str(request.body)))
            return Response201("Created")
        if query_type == "pools":
            self.storage.add_pool(json.loads(str(request.body)))
            return Response201("Created")
        elif query_type == "resources":
            self.storage.add_resource(json.loads(str(request.body)))
            return Response201("Created")
        else:
            return Response404("Don't know query_type "+query_type)
    
    def PUT(self, request, p, pool_id, resource_id):
        if p != 'pools':
            return Response500("PUT is reserved for adding resources to pools")
        self.storage.add_resource_to_pool(pool_id, resource_id)
        return Response201("Added "+resource_id+" to pool '"+pool_id+"'")
    
    def LOCK(self, request, r, resource_id):
        if r != "resources":
            return Response500("Only know how to lock resources not "+r)
        
        self.storage.lock_resource(resource_id)
        return Response('')
    
    def UNLOCK(self, request, r, resource_id):
        if r != "resources":
            return Response500("Only know how to unlock resources not "+r)
        
        self.storage.unlock_resource(resource_id)
        return Response('')
        
    def GET(self, request, query_type=None, resource_id=None):
        if query_type is None:
            # Get all descriptions
            pass
            
        # if query_type == "types":
        #     if resource_id is None:
        #         return JSONResponse(self.storage.get_all_types())
        #     else:
        #         return JSONResponse(self.storage.get_type(resource_id))
        if query_type == "pools":
            if resource_id is None:
                return JSONResponse(self.storage.get_all_pools())
            else:
                return JSONResponse(self.storage.get_pool(resource_id))
        elif query_type == "resources":
            if resource_id is None:
                return JSONResponse(self.storage.get_all_resources())
            else:
                return JSONResponse(self.storage.get_resource(resource_id))
            
        return Response404('Not a valid query type: '+query_type)