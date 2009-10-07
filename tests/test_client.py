from testbot import Client

def setup_module(module):
    module.c = Client('http://localhost:8888', 'testclient1')
    module.db = Database('http://localhost:5984/test_testbot')

def teardown_module(module):
    module.db.delete(module.db.get(module.c.client_info['_id']))
    


