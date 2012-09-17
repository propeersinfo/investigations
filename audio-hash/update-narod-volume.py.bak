# -*- coding: utf-8 -*-

""" update narod DB from HDD """
import json
import os
import pickle
import sys
import common

DB_ROOT = 'DB'
NAROD_VOL = 'temp'
NAROD_DIR = os.path.join(DB_ROOT, NAROD_VOL)
SUFFIX = None
#SUFFIX = 'new'

class BadHash(Exception):
  pass

def copy_track_info(src, dst):
  if src['album_hash'] != dst['album_hash']:
    raise BadHash()
  if len(src['tracks']) != len(dst['tracks']):
    raise BadHash()
  for t_src, t_dst in common.list_multiple_lists(src['tracks'], dst['tracks']):
    if t_src['audio_hash'] != t_dst['audio_hash']:
      raise BadHash()
  dst['tracks'] = src['tracks']


def main():
  for album_narod in common.list_db_volume(NAROD_DIR):
    assert album_narod.has_key('album_hash')
    assert album_narod.has_key('path')
    #print album['album_hash']
    sys.stdout.write('%s ' % album_narod['album_hash'])
    if os.path.exists(album_narod['path']):
      try:
        album_hdd = common.scan_album_from_dir(album_narod['path'])
        assert album_hdd
        #print 'hdd clone found'
        #new_dict = dict(album_narod)
        new_dict = common.Album(album_narod)
        copy_track_info(album_hdd, new_dict)
        eq = new_dict == album_narod

#        from utils import pretty_print_json_as_readable_unicode
#        f1 = '%s.old' % album_narod['album_hash']
#        f2 = '%s.new' % album_narod['album_hash']
#        common.write_file(f1, pretty_print_json_as_readable_unicode(album_narod))
#        common.write_file(f2, pretty_print_json_as_readable_unicode(new_dict))

        if not eq:
          common.save_db_album(DB_ROOT, NAROD_VOL, new_dict, suffix=SUFFIX)
          print 'updated'
        else:
          print 'not changed'
      except BadHash:
        print 'cannot update album'
    else:
      print 'the path does not exist anymore'


if __name__ == '__main__':
  main()