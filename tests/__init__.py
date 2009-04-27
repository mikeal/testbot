import os
import tempfile
import threading
from time import sleep
from testbot import MasterRestApplication, FileStorage
from cherrypy import wsgiserver

def setup_module(module):
    t = tempfile.mktemp(suffix="testbot.json")
    test_app = MasterRestApplication(FileStorage(t))
    
    httpd = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 8888), 
                       test_app, server_name='test_server', numthreads=50)
    module.httpd = httpd; module.thread = threading.Thread(target=httpd.start)
    module.thread.start()
    module.t = t
    sleep(.5)
    
def teardown_module(module):
    while module.thread.isAlive():
        module.httpd.stop()
    os.remove(t)