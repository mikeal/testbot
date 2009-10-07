from threading import Thread
from time import sleep

from couchquery import Database
from testbot import TestBotApplication
from wsgiref.simple_server import make_server


def setup_module(module):
    db = Database('http://localhost:5984/testbot')
    application = TestBotApplication(db)
    httpd = make_server('', 8888, application)
    print "Serving on http://localhost:8888/"
    thread = Thread(target=httpd.start)
    sleep(1)
    module.thread = thread
    module.httpd = httpd
    
def teardown_module(module):
    def teardown_module(module):
        while module.thread.isAlive():
            module.httpd.stop()