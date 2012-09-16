# -*- coding: utf-8 -*-
import shutil

import sys
import os

from utils import SafeStreamFilter, dict_of_lists
from common import  list_db_volume, check_hex_digest, load_db_volumes

DB_ROOT = '.\\DB'
MOVE_TARGET = 'D:\\move'


def do_try(really_do, removable_volume, albums_by_hash):
  if really_do and not os.path.exists(MOVE_TARGET):
    os.makedirs(MOVE_TARGET)

  to_remove_cnt = 0
  for album in list_db_volume(os.path.join(DB_ROOT, removable_volume)):
    ah = album['album_hash']
    copies = albums_by_hash.get(ah)
    if len(copies) > 2:
      assert False, len(copies)
    elif len(copies) == 2:
      to_remove_cnt += 1
      src = album['path']
      assert os.path.exists(src)
      parent, dir_short = dst = os.path.split(src)
      dst = os.path.join(MOVE_TARGET, dir_short)
      if os.path.exists(dst):
        dst = os.path.join(MOVE_TARGET, '%s-%s' % (ah, dir_short))
      if os.path.exists(dst):
        raise Exception('directory unexpectedly exists: %s' % dst)
      print '%s %s' % (ah, src)
      #print 'moving: %s' % src
      print '                             --> %s' % dst
      if really_do:
        shutil.move(src, dst)
        print 'moved'
  print '%d albums to remove from %s to %s' % (to_remove_cnt, removable_volume, MOVE_TARGET)


if __name__ == '__main__':
  SafeStreamFilter.substitute_stdout()

  base_name = os.path.splitext(sys.argv[0])[0]
  list_file = '%s.list' % base_name

  removable_volume = sys.argv[1]
  other_volumes, albums_by_hash = load_db_volumes(DB_ROOT, sys.argv[2], sys.argv[3])

  def do_try_cover(really_do):
    do_try(really_do, removable_volume, albums_by_hash)

  do_try_cover(False)
  sys.stdout.write("Confirm move (y/n): ")
  answer = sys.stdin.readline().strip().lower()
  if answer == 'y' or answer == 'yes':
    do_try_cover(True)
  else:
    print 'action aborted'