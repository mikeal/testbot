import os
import sys
from wsgiref.simple_server import make_server
from datetime import datetime

from couchquery import Database

this_directory = os.path.abspath(os.path.dirname(__file__))

design_dir = os.path.join(this_directory, 'design')
clients_design_dir = os.path.join(design_dir, 'clients')
jobs_design_dir = os.path.join(design_dir, 'jobs')

def create_job(db, job):
    job['type'] = 'job'
    job['creationdt'] = datetime.now().isoformat()
    job['status'] = 'pending'
    db.create(job)

def sync(db):
    db.sync_design_doc('clients', clients_design_dir)
    db.sync_design_doc('jobs', jobs_design_dir)

def cli():
    if not sys.argv[-1].startswith('http'):
        dburi = 'http://localhost:5984/testbot'
    else:
        dburi = sys.argv[-1]
    
    db = Database(dburi)
    sync(db)
    print "Using CouchDB @ "+dburi
    from testbot.server import TestBotApplication
    application = TestBotApplication(db, MozillaManager())
    httpd = make_server('', 8888, application)
    print "Serving on http://localhost:8888/"
    httpd.serve_forever()
    
class TestBotManager(object):
    pass    

class MozillaManager(object):
    """Logic for handling Mozilla's builds and tests"""
    
    def new_build(self, build):
        jobs = []
        for testtype in ['mochitest', 'reftest', 'mochitest-chrome']:
            jobs.append({'build':build, 'testtype':testtype})
        return jobs


    