import urllib2
import sys
DOWNLOAD_URL = 'http://localhost:8080/download/%s' % sys.argv[1]
print urllib2.urlopen(DOWNLOAD_URL).read()
