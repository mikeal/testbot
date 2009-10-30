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
    
    all_mobile_testtypes = [
        # Unittests
        'mochitest', 'mochitest-chrome', 'browser-chrome', 'reftest', 'crashtest', 
        'js-reftest', 'xpcshell',
        # Talos
        'talos-ts', 'talos-ts_cold', 'talos-ts_places_generated_max', 
        'talos-ts_places_generated_min', 'talos-ts_places_generated_med', 
        'talos-tp', 'talos-tp4', 'talos-tp_js', 'talos-tdhtml', 'talos-tgfx', 
        'talos-tsvg', 'talos-twinopen', 'talos-tjss', 'talos-tsspider', 
        'talos-tpan', 'talos-tzoom',
        ]
    
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
                    jobs.append({'build':build, 'jobtype':jobtype, 'package_uri':build_uri, 
                                 'tests_uri':tests_uri, 'platform':{'os.sysname':'Linux'},
                                 'product':'Firefox'})
            else:
                # Build is invalid
                build['invalid'] = True
                return None        
        elif build['branch'] == 'mobile-1.9.2-wince':
            tests_uri = [u for u in build['uris'] if u.endswith('.tests.tar.bz2')]
            winCE_package = [u for u in build['uris'] if u.endswith('.wince-arm.zip')]
            
            if len(winCE_package) is 0 or len(tests_uri) is 0:
                build['invalid'] = True
                return None # Build is invalid
            tests_uri = tests_uri[0]
            winCE_package = winCE_package[0]
            
            for jobtype in self.all_mobile_testtypes:
                jobs.append({'build':build, 'jobtype':jobtype, 'package_uri':winCE_package,
                             'tests_uri':tests_uri, 'product':'FirefoxCE', 
                             'platform':{'os.sysname':"WinCE", 'hardware':'Tegra'}})
        elif build['branch'] == 'mobile-1.9.2':
            fennec_uris = [u for u in build['uris'] if u.startswith('fennec')]
            xulrunner_uris = [u for u in build['uris'] if u.startswith('xulrunner')]

            # fennec builds currently don't produce a test package
            # fennec_tests_uri = [u for u in fennec_uris if u.endswith('.tests.tar.bz2')]
            # if len(fennec_tests_uri) is 0:
            #     build['invalid'] = True
            #     return None # Build is invalid
            
            xulrunner_tests_uri = [u for u in xulrunner_uris if u.endswith('.tests.tar.bz2')]
            if len(xulrunner_tests_uri) is 0:
                build['invalid'] = True
                return None # Build is invalid
            
            
            
        return jobs


    