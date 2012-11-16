import models
import base64
import json
import logging
import os
import time
from google.appengine.ext import db
from google.appengine.api import memcache

def generate_id():
    return base64.b64encode(os.urandom(6), '-_')


def error_message(user, data, message = ""):
    return json.dumps({'status': False,
                       'error': message})


def decode_and_validate(data):
    if not data:
        return None

    try:
        decoded = json.loads(data)
    except:
        return None

    if 'body' not in decoded and 'delete' not in decoded:
        return None

    if ('delete' in decoded or 'overwrite' in decoded) and\
        'authenticated' not in decoded:
        return None

    return decoded


def fetch_message(message_id, cache = False):
    message = memcache.get(message_id)
    if not message:
        q = db.GqlQuery('SELECT * FROM Message ' +
                        'WHERE deleted = False ' +
                        'AND message_id = :1 ' +
                        'AND expiry < :2 ' + 
                        'ORDER BY expiry DESC',
                        message_id, int(time.time()))
        message = q.get()
        if cache and message:
            memcache.add(message_id, message)

    if message and message.expiry < int(time.time()):
        message = None    
        memcache.delete(message_id)

    return message


def new_message(data, user, message_id = None, ip = None):
    if not message_id:
        message_id = generate_id()
    message = models.Message(message_id=generate_id(), body="<EMPTY>")
    message.body = data.get("body", "<EMPTY>")

    if len(message.body) > 2**24:
        return error_message(data, user, message = "Message too long")

    if "authenticated" in data and user:
        message.user = user
        username = user.email()
    else:
        username = "None"
    expiry = min(int(data.get('expiry', '60000')), 31557600)
    message.expiry = int(time.time()+expiry)
    if ip:
        message.ip_addr = ip
    message.put()
    memcache.set(message.message_id, message)
    output = {'message_id': message.message_id,
              'expiry': message.expiry,
              'user': username,
              'status': True}
    return json.dumps(output)
    

def overwrite_message(data, user, ip):
    old_id = data.get('overwrite', None)
    old_message = fetch_message(old_id)
    if not old_message:
        return error_message(data, user, message = "Overwrite error")
    if old_message.user.user_id() != user.user_id():
        return error_message(data, user, message = "Authentication error")

    old_message.deleted = True
    old_message.put()
    return new_message(data, user, message_id = old_id, ip = ip)


def delete_message(data, user, ip):
    old_id = data.get('delete', None)
    old_message = fetch_message(old_id)
    if not old_message:
        return error_message(data, user, message = "Delete error")
    if old_message.user.user_id() != user.user_id():
        return error_message(data, user, message = "Authentication error")

    old_message.deleted = True
    old_message.put()
    memcache.delete(old_id)
    return json.dumps({'status': True, 'message_id': old_id})


def process_command(data, user = None, ip = None):
    if 'body' in data and\
       'authenticated' in data and\
       'overwrite' in data and\
       user:
        return overwrite_message(data, user, ip=ip)
    
    if 'body' in data and\
       'authenticated' in data and\
       'delete' in data and\
       user:
        return overwrite_message(data, user, ip=ip)

    if 'body' in data:
        return new_message(data, user, ip=ip)

    return error_message(data, user, message = "Unknown command")
