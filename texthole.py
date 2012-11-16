from google.appengine.api import users
from google.appengine.ext import webapp

import common
import jinja2
import json
import logging
import time

env = jinja2.Environment(loader=jinja2.PackageLoader('texthole', 'templates'),
                         autoescape=True)

class UploadPage(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        self.response.headers['Content-Type'] = 'application/json'
        rawdata = self.request.get('data', None)
        if not rawdata:
            self.response.out.write(common.error_message(user,
                                                         None,
                                                         message = "No data"))
            return

        data = common.decode_and_validate(rawdata)
        if not data:
            self.response.out.write(common.error_message(user,
                                                         None,
                                                         message = "Bad data"))
            return
        ip = self.request.remote_addr
        self.response.out.write(common.process_command(data,
                                                       user,
                                                       ip=ip))
        return


class DownloadPage(webapp.RequestHandler):
    def get(self, tag):
        user = users.get_current_user()
        self.response.headers['Content-Type'] = 'application/json'
        message = common.fetch_message(tag)
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


class LogoutPage(webapp.RequestHandler):
    def get(self):
        if users.get_current_user():
            self.redirect(users.create_logout_url('/'))
        else:
            self.redirect('/')


mappings = [('/', MainPage),
            ('/upload', UploadPage),
            ('/download/([A-Za-z0-9_-]{8})', DownloadPage),
            ('/login', LoginPage),
            ('/logout', LogoutPage),
            ('/([A-Za-z0-9_-]{8})', MainPage)]


application = webapp.WSGIApplication(mappings, debug=True)
