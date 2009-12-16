try:
    import jsonlib2 as json
except:
    try:
        import yajl as json
    except:
        try:
            import simplejson as json
        except:
            import json

import couchdbviews
import uuid
from datetime import datetime
from couchquery import Database

def notification(func):
    def handle_notifications(doc, req):
        db = Database(req['db'])
        doc = json.loads(req['body'])
        doc['_id'] = str(uuid.uuid1())
        doc['type'] = 'notification'
        jobs = func(doc, req, db)
        for job in jobs:
            job['parent-notification'] = doc['_id']
            info = db.create(job)
            job['_id'] = info['id']
        doc['jobs'] = jobs
        return doc, json.dumps(doc)
    return couchdbviews.update_function(handle_notifications)

def get_job(func):
    def handle_get_job(doc, req):
        db = Database(req['db'])
        result = func(doc, req, db)
        if result:
            result['status'] = 'locked'
        return {'body':json.dumps(result), 'headers':{'Content-Type':'application/json'}}
    return couchdbviews.show_function(handle_get_job)

def report(func):
    def handle_report(doc, req):
        assert doc
        db = Database(req['db'])
        doc['status'] = 'done'
        result = func(doc, json.loads(req['body']), db)
        return doc, json.dumps(result)
    return couchdbviews.update_function(handle_report)

def heartbeat(func):
    def handle_heartbeat(doc, req):
        db = Database(req['db'])
        doc.update(json.loads(req['body']))
        doc['last_heartbeat'] = datetime.now().isoformat()
        doc = func(doc, req, db)
        return doc, json.dumps(doc)
    return couchdbviews.update_function(handle_heartbeat)