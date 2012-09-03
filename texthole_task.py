from google.appengine.ext import db
from google.appengine.ext import webapp

import models
import time

class ExpireTask(webapp.RequestHandler):
    def get(self):
        to_save = []
        q = db.GqlQuery('SELECT * FROM Message ' +
                        'WHERE deleted = False ' +
                        'AND expiry < :1', int(time.time()))
        for m in q:
            m.deleted = True
            to_save.append(m)

        db.put(to_save)

mappings = [('/task/expire', ExpireTask),]

application = webapp.WSGIApplication(mappings, debug=True)
