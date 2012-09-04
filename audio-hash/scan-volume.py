# -*- coding: utf-8 -*-

import sys
import os
import glob

from common import scan_album_from_dir
from common import NotAlbumException
from common import save_db_album
from utils import SafeStreamFilter

DB_ROOT = '.\\DB'


def init_db_volume(db_root, volume_name):
  ''' remove every regular file in the given directory '''
  dir = os.path.join(db_root, volume_name)

  if not os.path.exists(dir):
    os.mkdir(dir)

  for file_short in glob.glob1(dir, '*'):
    file_abs = os.path.join(dir, file_short)
    if os.path.exists(file_abs) and os.path.isfile(file_abs):
      os.remove(file_abs)


def main():
  SHOW_ONLY_FAILS = False
  assert len(sys.argv) >= 3
  root_dir = sys.argv[1]
  volume_name = sys.argv[2]
  if type(root_dir) == str:
    print 'decoding...'
    root_dir = root_dir.decode('windows-1251') # todo: how to rewrite that in a general way?
  assert os.path.exists(root_dir) and os.path.isdir(root_dir)
  init_db_volume(DB_ROOT, volume_name)
  album_cnt = 0
  for dir, subdirs, subfiles in os.walk(unicode(root_dir)):
    try:
      album = scan_album_from_dir(dir)
      if not SHOW_ONLY_FAILS:
        assert album is not None
        album_cnt += 1
        print u'album detected: %s' % dir
        save_db_album(DB_ROOT, volume_name, album)
    except NotAlbumException, e:
      if SHOW_ONLY_FAILS and e.code.serious:
        print u'%s: %s -> %s' % (e.code, dir, e.msg)
  print 'volume %s updated' % volume_name
  print '%d albums found' % album_cnt


if __name__ == '__main__':
  SafeStreamFilter.substitute_stdout()
  main()