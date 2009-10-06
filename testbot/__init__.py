import sys

from wsgiref.simple_server import make_server
from couchquery import Database
from webenv.rest import RestApplication

class TestBotApplication(RestApplication):
    def __init__(self, db):
        self.db = db

def cli():
    if not sys.argv[-1].startswith('http'):
        dburi = 'http://localhost:5984/testbot'
    else:
        dburi = sys.argv[-1]
    
    db = Database(dburi)
    print "Using CouchDB @ "+dburi
    application = TestBotApplication(db)
    httpd = make_server('', 8888, application)
    print "Serving on http://localhost:8888/"
    httpd.serve_forever()

