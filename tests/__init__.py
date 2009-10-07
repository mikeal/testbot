from threading import Thread
from time import sleep

from couchquery import Database, createdb, deletedb
from testbot import TestBotApplication
from wsgiref.simple_server import make_server


def setup_module(module):
    db = Database('http://localhost:5984/test_testbot')
    createdb(db)
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
    deletedb(db)