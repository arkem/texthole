from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import models

import base64
import os
import jinja2
import json
import time
import logging

env = jinja2.Environment(loader=jinja2.PackageLoader('texthole', 'templates'),
                         autoescape=True)


def generate_id():
    return base64.b64encode(os.urandom(6), '-_')

class UploadPage(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        self.response.headers['Content-Type'] = 'application/json'
        rawdata = self.request.get('data', None)
        if not rawdata:
            self.response.out.write(json.dumps({'status': False}))
            return
        try:
            data = json.loads(rawdata)
        except:
            self.response.out.write(json.dumps({'status': False}))
            return

        try:
            if 'body' not in data and 'delete' not in data:
                self.response.out.write(json.dumps({'status': False,
                                                    'error': 'No action'}))
                return
            message = models.Message(message_id=generate_id())
            authenticated = data.get('authenticated', None)
            old_id = None
            if authenticated:
                message.user = user
                message.put()
                if ('overwrite' in data or 'delete' in data) and user != None:
                    old_id = data.get('overwrite', None)
                    if not old_id:
                        old_id = data.get('delete', None)
                    oldmessage = memcache.get(old_id)
                    if not oldmessage:
                        q = db.GqlQuery('SELECT * FROM Message ' +
                                        'WHERE deleted = False ' +
                                        'AND message_id = :1 ' +
                                        'ORDER BY expiry DESC', old_id)
                        oldmessage = q.get()  # Don't cache this

                    if oldmessage.user.user_id() == user.user_id():
                        oldmessage.deleted = True
                        oldmessage.put()
                        message.message_id = old_id
                        # FIXME: If the put fails and the new message
                        # has a very short expiry then the old message may
                        # persist.
                        if 'delete' in data:
                            memcache.delete(old_id)
                            self.response.out.write(json.dumps(
                                {'status': True, 'message_id': old_id}))
                            return
                    else:
                        self.response.out.write(json.dumps(
                            {'status': False, 'error': 'Permission error'}))
                        return

            if len(data['body']) > 2**24:
                self.response.out.write(json.dumps({'status': False,
                                                    'error': 'Too long'}))
                return
            message.body = data['body']
            expiry = min(int(data.get('expiry', '60000')), 31557600)
            message.expiry = int(time.time()+expiry)
            message.ip_addr = self.request.remote_addr
            message.put()
            memcache.set(message.message_id, message)

            output = {'message_id': message.message_id,
                      'expiry': message.expiry,
                      'user': user.email(),
                      'status': True}
            self.response.out.write(json.dumps(output))
        except (KeyError, AttributeError, ValueError):
            self.response.out.write(json.dumps({'status': False}))
        
class DownloadPage(webapp.RequestHandler):
    def get(self, tag):
        user = users.get_current_user()
        self.response.headers['Content-Type'] = 'application/json'
        message = memcache.get(tag)
        if not message:
            q = db.GqlQuery('SELECT * FROM Message WHERE deleted = False ' +
                            'AND message_id = :1 ORDER BY expiry DESC', tag)
            message = q.get()
            memcache.add(tag, message)

        output = {}
        if message:
            output['body'] = message.body
            output['expiry'] = message.expiry
            output['message_id'] = message.message_id
            output['created'] = int(time.mktime(message.created.timetuple()))
            output['editable'] = (user != None and message.user != None and
                                  user.user_id() == message.user.user_id())
            output['status'] = True
        else:
            output['status'] = False
            output['message_id'] = tag
            output['error'] = 'Not found'

        self.response.out.write(json.dumps(output))


class MainPage(webapp.RequestHandler):
    def get(self, tag=None):
        user = users.get_current_user()
        if user:
            email = user.email()
        else:
            email = None
        template = env.get_template('main.html')
        self.response.out.write(template.render(tag=tag,
                                                user=email))
        return

class LoginPage(webapp.RequestHandler):
    def get(self):
        if not users.get_current_user():
            self.redirect(users.create_login_url('/'))
        else:
            self.redirect('/')

mappings = [('/', MainPage),
            ('/upload', UploadPage),
            ('/download/([A-Za-z0-9_-]{8})', DownloadPage),
            ('/login', LoginPage),
            ('/([A-Za-z0-9_-]{8})', MainPage)]

application = webapp.WSGIApplication(mappings, debug=True)
