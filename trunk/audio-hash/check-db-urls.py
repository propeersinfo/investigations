# -*- coding: utf-8 -*-

import json
import os
from time import sleep
from urlparse import urlparse
import httplib
import sys

import common

def check_url(url):
  urlp = urlparse(url)
  assert urlp.netloc.lower() == 'narod.ru'
  conn = httplib.HTTPConnection(urlp.netloc)
  conn.request('GET', urlp.path)
  r = conn.getresponse()
  location = r.getheader('Location')
  if r.status == 200:
    return True
  elif r.status == 302 and location and location.find('/404') >= 0:
    return False
  else:
    raise Exception('unexpected response from server - that could be interesting')

NAROD_DB = 'DB/narod'

total = 0
passed = 0
failed = 0

assert os.path.exists(NAROD_DB)
for file in os.listdir(NAROD_DB):
  if common.check_hex_digest(file):
    album = json.loads(common.read_file(os.path.join(NAROD_DB, file)))
    url = album['url']
    ok = check_url(album['url'])
    sys.stderr.write('.')
    if total % 10 == 0: sys.stderr.write('.%s.' % total)
    if ok:
      passed += 1
    else:
      failed += 1
      #ok_str = 'ok' if ok else '404'
      #print '%-4s %s %s ...' % (ok_str, album['album_hash'], url[0:40])
      sys.stderr.write('.%s.' % album['album_hash'])
    sleep(1)
    total += 1

print ''
print 'total=%d pass=%d fail=%d' % (total, passed, failed)