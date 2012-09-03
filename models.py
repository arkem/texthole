from google.appengine.ext import db

class Message(db.Model):
    body = db.TextProperty(required=True)
    user = db.UserProperty()
    expiry = db.IntegerProperty(default=0)
    deleted = db.BooleanProperty(default=False)
    ip_addr = db.StringProperty()
    message_id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

