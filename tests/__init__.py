from threading import Thread
from time import sleep
from wsgiref.simple_server import make_server

from couchquery import Database, createdb, deletedb

from testbot import sync
from testbot.server import TestBotApplication


def setup_module(module):
    db = Database('http://localhost:5984/test_testbot')
    createdb(db)
    sync(db)
    application = TestBotApplication(db)
    httpd = make_server('', 8888, application)
    print "Serving on http://localhost:8888/"
    thread = Thread(target=httpd.serve_forever)
    thread.start()
    sleep(1)
    module.thread = thread
    module.httpd = httpd
    module.db = db
    
def teardown_module(module):
    module.httpd.shutdown()
    while module.thread.isAlive():
        sleep(.5)    
    deletedb(module.db)