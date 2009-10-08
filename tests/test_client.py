from couchquery import Database

from testbot import create_job
from testbot.client import Client

class TestClient(Client):
    jobtypes = ['test']
    jobs_completed = []
    heartbeat_interval = 1
    waiting_sleep = 1
    
    def do_job(self, job):
        self.jobs_completed.append(job)
        if job['jobname'] == 'test99':
            self.running = False
        return {"passed":True}    

def setup_module(module):
    module.c = TestClient('http://localhost:8888', 'testclient1')
    module.db = Database('http://localhost:5984/test_testbot')
    
def test_do_all_jobs():
    for x in range(100):
        create_job(db, {"jobtype":'test', "jobname":"test"+str(x)})
    print 'doing test'
    c.run()

def teardown_module(module):
    module.db.delete(module.db.get(module.c.client_info['_id']))
    


