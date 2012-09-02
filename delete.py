import urllib2
import urllib
import sys
import json

UPLOAD_URL = 'http://localhost:8080/upload'

message = {}

if len(sys.argv) > 1:
    message['authenticated'] = True
if len(sys.argv) > 2:
    message['delete'] = sys.argv[2]
data = urllib.urlencode({'data': json.dumps(message)})
req = urllib2.Request(UPLOAD_URL, data)
if len(sys.argv) > 1:
    req.add_header('Cookie', sys.argv[1])
print urllib2.urlopen(req).read()
