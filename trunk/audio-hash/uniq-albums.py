# -*- coding: utf-8 -*-

import sys
import os
import codecs

from utils import SafeStreamFilter
from utils import format_size_mb
from common import Album, load_db_volumes


DB_ROOT = '.\\DB'


def _get_volumes_and_uniq_hashes():
  volumes, albums_by_hash = load_db_volumes(DB_ROOT)
  hashes_unique = [ albums[0] for hash, albums in albums_by_hash.items() if len(albums) == 1]
  return volumes, hashes_unique


if __name__ == '__main__':
  SafeStreamFilter.substitute_stdout()

  base_name = os.path.splitext(sys.argv[0])[0]
  list_file = '%s.list' % base_name

  volumes, hashes_unique = _get_volumes_and_uniq_hashes()
  hashes_unique = sorted(hashes_unique, key=lambda album: album['path'])
  with codecs.open(list_file, 'w', 'utf-8') as f:
    for album in hashes_unique:
      album = Album(album)
      dir = album['path']
      dir_size = album['total_size']
      fmt = album.get_audio_format()
      line = u'%s %4s %-4s %s' % (album['album_hash'], format_size_mb(dir_size), fmt, dir)
      print >> f, line
      print >> sys.stdout, line
