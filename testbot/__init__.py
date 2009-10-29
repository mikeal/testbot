import os
import sys
import random
from wsgiref.simple_server import make_server
from datetime import datetime

from couchquery import Database
from webenv.applications.file_server import FileServerApplication

this_directory = os.path.abspath(os.path.dirname(__file__))

design_dir = os.path.join(this_directory, 'design')
static_dir = os.path.join(this_directory, 'static')
clients_design_dir = os.path.join(design_dir, 'clients')
jobs_design_dir = os.path.join(design_dir, 'jobs')
builds_design_dir = os.path.join(design_dir, 'builds')
mozilla_design_dir = os.path.join(design_dir, 'mozilla')

def create_job(db, job):
    job['type'] = 'job'
    job['creationdt'] = datetime.now().isoformat()
    job['status'] = 'pending'
    db.create(job)

def sync(db):
    db.sync_design_doc('clients', clients_design_dir)
    db.sync_design_doc('jobs', jobs_design_dir)
    db.sync_design_doc('builds', builds_design_dir)
    db.sync_design_doc('mozilla', mozilla_design_dir)

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
    application.add_resource('static', FileServerApplication(static_dir))
    httpd = make_server('', 8888, application)
    print "Serving on http://localhost:8888/"
    httpd.serve_forever()
    
class TestBotManager(object):
    pass    

class MozillaManager(object):
    """Logic for handling Mozilla's builds and tests"""
    
    def get_job(self, client):
        if client['platform'].get('os.sysname', None) == 'Linux':
            if client['platform'].get('os.linux.distrobution',[]).get(0,None) == 'CentOS':
                # Desktop linux
                supported_jobtypes = client['jobtypes']
                
                while len(supported_jobtypes) is not 0:
                    jtype = random.sample(supported_jobtypes, 1)[0]
                    result = self.db.views.mozilla.desktopBuilds(
                        startkey=['Linux', jtype, {}], endkey=['Linux', jtype, None], 
                        descending=True, limit=1)
                    if len(result) is not 0:
                        return result[0]
                    supported_jobtypes.remove(jtype)
                # No jobs were found
                return None
    
    def new_build(self, build):
        jobs = []
        
        if build['branch'] == 'mozilla-central-linux':
            build_uri = [u for u in build['uris'] if u.endswith('.en-US.linux-i686.tar.bz2')]
            tests_uri = [u for u in build['uris'] if u.endswith('.en-US.linux-i686.tests.tar.bz2')]
            if len(build_uri) is 1 and len(tests_uri) is 1:
                build_uri = build_uri[0]
                tests_uri = tests_uri[0]    
                for jobtype in ['mochitest', 'reftest', 'mochitest-chrome']:
                    jobs.append({'build':build, 'jobtype':jobtype, 'build_uri':build_uri, 'tests_uri':tests_uri, 'platform':{'os.sysname':'Linux'}})
            else:
                # Build is invalid
                build['invalid'] = True
        return jobs


    