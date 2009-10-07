import os
import sys
from time import sleep
from threading import Thread

try:
    import json
except:
    import simplejson as json

from httplib2 import Http

http = Http()

class ClientException(Exception): pass

class JobException(Exception): pass

class Client(object):
    heartbeat_interval = 60
    waiting_sleep = 60
    job_types = []
    
    def __init__(self, server_uri, name):
        if not server_uri.endswith('/'):
            server_uri += '/'
        self.server_uri = server_uri
        self.name = name
        self.registered = False
        self.running = False
        self.heartbeat_running = False
    
    def register(self):
        resp, content = http.request(self.server_uri+'api/whoami?name='+self.name, method="GET")
        if resp.status == 200:
            self.client_info = json.loads(content)
            self.client_info['capabilities'] = self.capabilities
            self.client_info['heartbeat_interval'] = self.heartbeat_interval
            self.registered = True
        else:
            raise ClientException("Whoami failed for name "+self.name+'\n'+content)
    
    @property
    def capabilities(self):
        return self.get_default_capabilities()
    
    def get_default_capabilities(self):
        # Get the operating system and all that jazz     
        sysname, nodename, release, version, machine = os.uname()
        sysinfo = {'os.name':sysname, 'hostname':nodename, 'os.version.number':release,
                   'os.version.string':version, 'arch':machine}
        if sys.platform == 'darwin':
            import platform
            sysinfo['mac_ver'] = platform.mac_ver()
        elif sys.platform == 'linux2':
            import platform
            sysinfo['linux_distrobution'] = platform.linux_distrobution()
            sysinfo['libc_ver'] = platform.libc_ver()           
        return {'capabilities':{'sysinfo':sysinfo},'jobtypes':self.jobtypes}
        
    def get_job(self):
        resp, content = http.request(self.server_uri+'api/getJob', method='POST', body=json.dumps(self.client_info))
        if resp.status == 200:
            job = json.loads(content)
            self.client_info['job'] = job
            return job
        elif resp.status == 204:
            return None
        else:
            raise ClientException("getJob failed \n"+content) 
        
    def run(self):
        if self.registered is False:
            self.register()
        self.client_info['status'] = 'available'
        self.start_heartbeat()
        self.running = True
        while self.running is True:
            job = self.get_job()
            if job is None:
                sleep(self.waiting_sleep)
            else:
                self.client_info['status'] = 'busy'
                self.push_status()
                result = self._do_job(job)
                if type(result) != JobException:
                    self.report(job, result)
                self.client_info['status'] = 'available'
                self.push_status()
    
    def heartbeat(self):
        assert self.heartbeat_running is False
        while self.heartbeat_running:
            self.push_status()
            sleep(self.heartbeat_interval)
    
    def start_heartbeat(self):
        self.heartbeat_thread = Thread(target=self.run)
        self.heartbeat_thread.start()
        return self.heartbeat_thread
    
    def stop_heartbeat(self):
        while self.heartbeat_thread.isAlive():
            self.heartbeat_running = False
            sleep(self.heartbeat_interval / 4)    
    
    def push_status(self):
        resp, content = http.request(self.server_uri+'api/heatbeat/'+self.client_info['_id'], method='POST', body=json.dumps(self.client_info))
        assert resp.status == 200
    
    def _do_job(self, job):
        if not hasattr(self, 'do_job'):
            raise NotImplemented("You must implement a client.do_job function()")
        try:
            return self.do_job(job)
        except:
            pass # TODO: Exception handling
    
    def start(self):
        self.thread = Thread(target=self.run)
        self.thread.start()
        return self.thread
    
    def stop(self):
        while self.thread.isAlive():
            self.running = False
            sleep(self.waiting_sleep / 4)
        