try:
    import json
except:
    import simplejson as json

import httplib2

master_url = "http://localhost:8888"

def r(method, path, body=None):
    """Do request to test server"""
    h = httplib2.Http()
    return h.request(master_url+path, method, body=json.dumps(body), headers={'content-type':'application/json'})
    

def test_creation():
    # rtype = {"type_id":"test-resource"}
    # resp, content = r("POST", "/types", body=rtype)
    # assert resp.status == 201
    # 
    # resp, content = r("GET", "/types/test-resource")
    # assert resp.status == 200
    # assert json.loads(content) == rtype
    
    resource = {"resource_id":"test-resource1", "resource_type":"test-resource"}
    resp, content = r("POST", "/resources", body=resource)
    assert resp.status == 201
    
    resp, content = r("GET", "/resources/test-resource1")
    assert resp.status == 200
    assert json.loads(content) == resource
    
    pool = {"pool_id":"pool1"}
    resp, content = r("POST", "/pools", body=pool)
    assert resp.status == 201
    
    resp, content = r("GET", "/pools/pool1")
    assert resp.status == 200
    assert json.loads(content) == pool
    
def test_add_resource_to_pool():
     
     
    
    
    