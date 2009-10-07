try:
    import json
except:
    import simplejson as json

from httplib2 import Http

http = Http()

class ClientException(Exception): pass

class Client(object):
    def __init__(self, server_uri, name):
        if not server_uri.endswith('/'):
            server_uri += '/'
        self.server_uri = server_uri
        self.name = name
        self.registered = False
    
    def register(self):
        resp, content = http.request(self.server_uri+'api/whoami?name='+self.name, method="GET")
        if resp.status == 200:
            self.client_info = json.loads(content)
            self.client_info['capabilities'] = self.capabilities
            self.registered = True
        else:
            raise ClientException("Whoami failed for name "+name+'\n'+content)
    
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
        return {'capabilities':{'sysinfo':sysinfo}}
        
    def get_job(self):
        resp, content = http.request(self.server_uri+'api/getJob', method=POST, body=json.dumps(self.client_info))
        if resp.status == 200:
            job = json.loads(content)
            self.client_info['job'] = job
            return job
        elif resp.status == 204:
            return None
        else:
            raise ClientException("getJob failed \n"+content) 
        
        
        