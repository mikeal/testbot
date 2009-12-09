import os
import sys
from time import sleep
from threading import Thread
import httplib2

try:
    import json
except:
    import simplejson as json

class Http(httplib2.Http):
    def request(self, uri, method="GET", body=None, headers=None, redirections=httplib2.DEFAULT_MAX_REDIRECTS, connection_type=None):
        """request handler with thread safety hacked in"""
        try:
            if headers is None:
                headers = {}
            else:
                headers = httplib2._normalize_headers(headers)
            if not headers.has_key('user-agent'):
                headers['user-agent'] = "Python-httplib2/%s" % httplib2.__version__
            uri = httplib2.iri2uri(uri)
            (scheme, authority, request_uri, defrag_uri) = httplib2.urlnorm(uri)
            domain_port = authority.split(":")[0:2]
            if len(domain_port) == 2 and domain_port[1] == '443' and scheme == 'http':
                scheme = 'https'
                authority = domain_port[0]
            conn_key = scheme+":"+authority
            def get_conn(conn_key):
                if conn_key in self.connections:
                    conn = self.connections[conn_key]
                    if type(conn) is list:
                        for c in conn:
                            if not getattr(c, 'busy', True):
                                return c
                    else: return c
                    if type(conn) is list:
                        return None
            conn = get_conn(conn_key)
            if conn is None:
                if not connection_type:
                    connection_type = (scheme == 'https') and httplib2.HTTPSConnectionWithTimeout or httplib2.HTTPConnectionWithTimeout
                certs = list(self.certificates.iter(authority))
                if scheme == 'https' and certs:
                    conn = connection_type(authority, key_file=certs[0][0],
                        cert_file=certs[0][1], timeout=self.timeout, proxy_info=self.proxy_info)
                    self.connections.setdefault(conn_key, []).append(conn)
                else:
                    conn = connection_type(authority, timeout=self.timeout, proxy_info=self.proxy_info)
                    self.connections.setdefault(conn_key, []).append(conn) 
                conn.set_debuglevel(httplib2.debuglevel)
            conn.busy = True
            if method in ["GET", "HEAD"] and 'range' not in headers and 'accept-encoding' not in headers:
                headers['accept-encoding'] = 'deflate, gzip'
            info = httplib2.email.Message.Message()
            cached_value = None
            if self.cache:
                cachekey = defrag_uri
                cached_value = self.cache.get(cachekey)
                if cached_value:
                    try:
                        info, content = cached_value.split('\r\n\r\n', 1)
                        feedparser = httplib2.email.FeedParser.FeedParser()
                        feedparser.feed(info)
                        info = feedparser.close()
                        feedparser._parse = None
                    except IndexError:
                        self.cache.delete(cachekey)
                        cachekey = None
                        cached_value = None
            else: cachekey = None
            if method not in ["GET", "HEAD"] and self.cache and cachekey:
                # RFC 2616 Section 13.10
                self.cache.delete(cachekey)
            if cached_value and method in ["GET", "HEAD"] and self.cache and 'range' not in headers:
                if info.has_key('-x-permanent-redirect-url'):
                    (response, new_content) = self.request(info['-x-permanent-redirect-url'], "GET", headers = headers, redirections = redirections - 1)
                    response.previous = Response(info)
                    response.previous.fromcache = True
                else:
                    entry_disposition = httplib2._entry_disposition(info, headers) 
                    if entry_disposition == "FRESH":
                        if not cached_value:
                            info['status'] = '504'
                            content = ""
                        response = Response(info)
                        if cached_value:
                            response.fromcache = True
                        return (response, content)
                    if entry_disposition == "STALE":
                        if info.has_key('etag') and not self.ignore_etag and not 'if-none-match' in headers:
                            headers['if-none-match'] = info['etag']
                        if info.has_key('last-modified') and not 'last-modified' in headers:
                            headers['if-modified-since'] = info['last-modified']
                    elif entry_disposition == "TRANSPARENT": pass
                    (response, new_content) = self._request(conn, authority, uri, request_uri, method, body, headers, redirections, cachekey)
                if response.status == 304 and method == "GET":
                    # Rewrite the cache entry with the new end-to-end headers
                    # Take all headers that are in response 
                    # and overwrite their values in info.
                    # unless they are hop-by-hop, or are listed in the connection header.

                    for key in httplib2._get_end2end_headers(response):
                        info[key] = response[key]
                    merged_response = Response(info)
                    if hasattr(response, "_stale_digest"):
                        merged_response._stale_digest = response._stale_digest
                    httplib2._updateCache(headers, merged_response, content, self.cache, cachekey)
                    response = merged_response
                    response.status = 200
                    response.fromcache = True 

                elif response.status == 200:
                    content = new_content
                else:
                    self.cache.delete(cachekey)
                    content = new_content 
            else: 
                cc = httplib2._parse_cache_control(headers)
                if cc.has_key('only-if-cached'):
                    info['status'] = '504'
                    response = Response(info)
                    content = ""
                else:
                    (response, content) = self._request(conn, authority, uri, request_uri, method, body, headers, redirections, cachekey)
        except Exception, e:
            if self.force_exception_to_status_code:
                if isinstance(e, httplib2.HttpLib2ErrorWithResponse):
                    response = e.response
                    content = e.content
                    response.status = 500
                    response.reason = str(e) 
                elif isinstance(e, socket.timeout):
                    content = "Request Timeout"
                    response = Response( {
                            "content-type": "text/plain",
                            "status": "408",
                            "content-length": len(content)
                            })
                    response.reason = "Request Timeout"
                else:
                    content = str(e) 
                    response = Response( {
                            "content-type": "text/plain",
                            "status": "400",
                            "content-length": len(content)
                            })
                    response.reason = "Bad Request" 
            else: raise
        return (response, content)

http = Http()

class ClientException(Exception): pass

class JobException(Exception): pass

class Client(object):
    heartbeat_interval = 60
    waiting_sleep = 60
    jobtypes = []
    
    def __init__(self, server_uri, name):
        if not server_uri.endswith('/'):
            server_uri += '/'
        self.server_uri = server_uri
        self.name = name
        self.registered = False
        self.running = False
        self.heartbeat_running = False
    
    def register(self):
        resp, content = http.request(self.server_uri+'api/whoami?name='+self.name, method="GET")
        if resp.status == 200:
            self.client_info = json.loads(content)
            self.client_info['capabilities'] = self.capabilities
            self.client_info['heartbeat_interval'] = self.heartbeat_interval
            self.registered = True
        else:
            raise ClientException("Whoami failed for name "+self.name+'\n'+content)
    
    @property
    def capabilities(self):
        return {'platform':self.platform, 'jobtypes':self.jobtypes}
    
    @property
    def platform(self):
        sysname, nodename, release, version, machine = os.uname()
        sysinfo = {'os.sysname':sysname, 'os.hostname':nodename, 'os.version.number':release,
                   'os.version.string':version, 'os.arch':machine}
        if sys.platform == 'darwin':
            import platform
            sysinfo['os.mac.version'] = platform.mac_ver()
        elif sys.platform == 'linux':
            import platform
            sysinfo['os.linux.distribution'] = platform.linux_distribution()
            sysinfo['os.libc.ver'] = platform.libc_ver()
        return sysinfo
        
    def get_job(self):
        print "get_job uri = " + self.server_uri + 'api/getJob'
        resp, content = http.request(self.server_uri+'api/getJob', method='POST', body=json.dumps(self.client_info))
        assert resp
        if resp.status == 200:
            job = json.loads(content)
            self.client_info['job'] = job
            return job
        elif resp.status == 204:
            return None
        else:
            raise ClientException("getJob failed \n"+content) 
        
    def run(self):
        if self.registered is False:
            self.register()
        self.client_info['status'] = 'available'
        self.start_heartbeat()
        self.running = True
        while self.running is True:
            job = self.get_job()
            if job is None:
                sleep(self.waiting_sleep)
            else:
                self.client_info['status'] = 'busy'
                self.push_status()
                result = self._do_job(job)
                if type(result) != JobException:
                    self.report(job, result)
                self.client_info['status'] = 'available'
                self.push_status()
    
    def heartbeat(self):
        assert self.heartbeat_running is False
        while self.heartbeat_running:
            self.push_status()
            sleep(self.heartbeat_interval)
    
    def start_heartbeat(self):
        self.heartbeat_thread = Thread(target=self.heartbeat)
        self.heartbeat_thread.start()
        return self.heartbeat_thread
    
    def stop_heartbeat(self):
        while self.heartbeat_thread.isAlive():
            self.heartbeat_running = False
            sleep(self.heartbeat_interval / 4)    
    
    def push_status(self):
        resp, content = http.request(self.server_uri+'api/heartbeat/'+self.client_info['_id'], method='POST', body=json.dumps(self.client_info))
        assert resp.status == 200
        info = json.loads(content)
        self.client_info['_rev'] = info['rev']
    
    def report(self, job, result):
        resp, content = http.request(self.server_uri+'api/report/'+job['_id'], method='POST', body=json.dumps(result))
        assert resp.status == 200
        if not content:
            return None
        return json.loads(content)
    
    def _do_job(self, job):
        if not hasattr(self, 'do_job'):
            raise NotImplemented("You must implement a client.do_job function()")
        try:
            return self.do_job(job)
        except:
            pass # TODO: Exception handling
    
    def start(self):
        self.thread = Thread(target=self.run)
        self.thread.start()
        return self.thread
    
    def stop(self):
        while self.thread.isAlive():
            self.running = False
            sleep(self.waiting_sleep / 4)
        
