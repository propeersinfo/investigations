# -*- coding: utf-8 -*-

import sys
import json
import re
import os
import glob
import codecs
import hashlib

from common import SafeStreamFilter
from common import dict_of_lists
from common import check_hex_digest
from common import format_size_mb
from common import Album


DB_ROOT = '.\\DB'


def get_volumes():
  volumes = []
  all_album_hashes = dict_of_lists()
  for volume_name in os.listdir(DB_ROOT):
    volume_dir = os.path.join(DB_ROOT, volume_name)
    if not os.path.isdir(volume_dir):
      continue
    volume = {
      'name': volume_name,
    }
    volumes.append(volume)
    for album_json_short in os.listdir(volume_dir):
      if check_hex_digest(album_json_short):
        album_json_abs = os.path.join(volume_dir, album_json_short)
        try:
          with codecs.open(album_json_abs, 'r', 'utf-8') as f:
            album_obj = json.loads(f.read())
            ah = album_obj['album_hash']
            assert ah == album_json_short, '%s vs %s' % (ah, album_json_short)
            volume[ah] = album_obj
            all_album_hashes.append(ah, album_obj)
        except BaseException, e:
          print 'cannot read file %s' % album_json_abs
          raise

  hashes_unique = [ albums[0] for hash, albums in all_album_hashes.items() if len(albums) == 1]
  #hashes_duplicated = [ (hash,albums)    for hash,albums in all_album_hashes.items() if len(albums) >  1 ]
  return volumes, hashes_unique#, hashes_duplicated


if __name__ == '__main__':
  SafeStreamFilter.substitute_stdout()

  base_name = os.path.splitext(sys.argv[0])[0]
  list_file = '%s.list' % base_name

  volumes, hashes_unique = get_volumes()
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
