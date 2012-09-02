from google.appengine.ext import db

class Message(db.Model):
    body = db.TextProperty()
    user = db.UserProperty()
    expiry = db.IntegerProperty()
    deleted = db.BooleanProperty(default=False)
    ip_addr = db.StringProperty()
    message_id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

