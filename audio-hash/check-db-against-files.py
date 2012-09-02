import json
import os

import common

'''
Check DB entries against a real directory (referred by key 'path')
'''

volume = "DB\\narod"

common.SafeStreamFilter.substitute_stdout()

for file in os.listdir(volume):
  if common.check_hex_digest(file):
    file = os.path.join(volume, file)
    with open(file, 'r') as f:
      a = json.loads(f.read())
      print '%s ...' % a['path']

      assert os.path.exists(a['path'])
      assert a['album_hash']
      assert a['url'].find('narod') >= 0

      a2 = common.scan_album_dir(a['path'], common.collect_audio_hashes())
      assert a2
      assert a['album_hash'] == a2['album_hash'], '%s vs %s' % (a['album_hash'], a2['album_hash'])
      assert len(a['tracks']) == len(a2['tracks'])
      for i,t in enumerate(a['tracks']):
        th1 = a['tracks'][i]['audio_hash']
        th2 = a2['tracks'][i]['audio_hash']
        assert th1
        assert th2
        assert th1 == th2