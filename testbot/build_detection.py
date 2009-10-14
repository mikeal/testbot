import os
import sys
import json
import optparse
from xml.etree import ElementTree

import httplib2
from pyquery import PyQuery

products = {'firefox':
                {'uri':'http://ftp.mozilla.org/pub/mozilla.org/firefox/tinderbox-builds/',
                 'branches':['mozilla-central-linux', 'mobile-1.9.2'],
                },
           }

def NaN(i):
    try: int(i)        
    except: return True
    return False
           
class BuildChecker(object):           
    """Checks a collection of products and branches for new builds."""
    def __init__(self, products, testbot_uri, cache=None):
        if cache is None:
            cache = {}
        self.cache = cache
        self.products = products
        if not testbot_uri.endswith('/'):
            testbot_uri += '/'
        self.testbot_uri = testbot_uri
        self.http = httplib2.Http()
        
    def parse_build_page(self, base_uri, d):
        tarballs = [n for n in d("a") if '.' in n.text]
        
        buildinfo = {'uris':[base_uri + n.text for n in tarballs]}  
        return buildinfo
    

    def check_product(self, name, info):
        for branch in info['branches']:
            url = info['uri'] + branch
            resp, content = self.http.request(url)
            d = PyQuery(content)
            known_builds = sorted(self.cache.setdefault(name, {}).setdefault(
                                                        branch, {}).setdefault('builds', []))
            new_builds = [n.text[:-1] for n in d("a") if ( not NaN(n.text[:-1]) ) and (
                                                           n.text[:-1] not in known_builds )]
            for build in new_builds:
                base_uri = url + '/' + build + '/'
                resp, content = self.http.request(base_uri)
                d = PyQuery(content)
                build_info = self.parse_build_page(base_uri, d)
                build_info.update({'product':name, 'branch':branch, 'buildid':build, })
                resp, content = self.http.request(self.testbot_uri + 'api/newBuild', method='POST', 
                                                  body=json.dumps(build_info)) 
                assert resp.status == 200
                self.cache[name][branch]['builds'].append(build)
                
                

    def check_all_builds(self):
        for product, info in products.items():
            result = self.check_product(product, info)
    

def cli():
    parser = optparse.OptionParser()
    parser.add_option("-c", "--cache", dest="cachefile", help="Path to cache filename.", default=None)
    parser.add_option("-t", "--testbot", dest="testbot", help="URL to testbot server.", default=None)
    options, args = parser.parse_args()
    
    if options.cachefile is not None:
        cache = json.loads(open(options.cachefile, 'r').read())
    else: cache = None
    
    if not options.testbot:
        print 'You must specify a testbot server to report to.'
        sys.exit(1)
    
    bc = BuildChecker(products, options.testbot, cache=cache)
    bc.check_all_builds()
    print 'done'
    bc.check_all_builds()

if __name__ == "__main__":
    cli()