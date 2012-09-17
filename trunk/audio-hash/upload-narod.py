# -*- coding: utf-8 -*-

import sys
import json
import re
import os
import glob
import codecs
import hashlib
import subprocess
from time import sleep

from common import archive_dir, empty_files
from common import calc_album_hash
from common import get_audio_files
from common import collect_audio_hashes
from common import scan_album_from_dir
from common import save_db_album
from common import append_file
from utils import SafeStreamFilter

QUEUE_FILE = 'upload.queue'
ACTUAL_ZIP_AND_UPLOAD = True
DB_ROOT = '.\\DB'
NAROD_VOLUME = 'narod'
ARCHIVE_TEMP_DIR = 'd:\\temp'
HASH_DB_FILE = 'audio_hash_edge.txt'
SLEEP_SEC = 5
FAILURE_LIST = 'upload-narod.failure'
SUCCESS_LIST = 'upload-narod.success'


def do_upload(zip_file):
  cmd = ['up-arkiv.bat', zip_file]

  print 'running process: %s' % cmd
  sys.stdout.flush()

  if ACTUAL_ZIP_AND_UPLOAD:
    #p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p = subprocess.Popen(cmd, stdin=None, stdout=subprocess.PIPE, stderr=None)
    stdout = p.stdout.read()
  #stderr = p.stderr.read()
  else:
    stdout = 'http://narod.ru/xxx'
  #stderr = 'errrrr'

  print 'logging stdout:'
  print stdout

  #print 'logging stderr:'
  #print '-disabled-' # stderr

  stdout = stdout.strip()
  if stdout.lower().find('http://') == 0:
    print 'file uploaded OK'
    return stdout
  else:
    print 'WARNING! file NOT uploaded'
    return None


def handle_dir(dir, hash_check, is_last_iteration):
  audio_files, _ = get_audio_files(dir)
  hash_actual = calc_album_hash(dir) # todo: handle NotAlbumException
  if hash_check:
    assert type(hash_check) == str, type(hash_check)
    assert type(hash_actual) == str, type(hash_actual)
    assert hash_check == hash_actual, '%s vs %s' % (hash_check, hash_actual)

  db_album_file = os.path.join(DB_ROOT, NAROD_VOLUME, hash_actual)
  if os.path.exists(db_album_file):
    #append_file(FAILURE_LIST, '%s %s' % (hash1, dir))
    print ''
    print 'WARINIG! db_album_file already exists: %s' % db_album_file
    print 'No zip, no upload'
    print ''
  else:
    archive_file = os.path.join(ARCHIVE_TEMP_DIR, '%s.zip' % hash_actual)
    print 'zipping into %s...' % archive_file
    if ACTUAL_ZIP_AND_UPLOAD:
      archive_dir(dir, archive_file)

    sys.stdout.flush()

    narod_url = do_upload(archive_file)
    if narod_url:
      if ACTUAL_ZIP_AND_UPLOAD:
        album_obj = scan_album_from_dir(dir)
        album_obj['url'] = narod_url
        album_obj['total_size'] = os.stat(archive_file).st_size
        #print 'WARNING! db file not written!'
        save_db_album(DB_ROOT, NAROD_VOLUME, album_obj)
      append_file(SUCCESS_LIST, '%s %s' % (hash_actual, dir))

      if not is_last_iteration and ACTUAL_ZIP_AND_UPLOAD:
        print 'sleeping for %s seconds' % SLEEP_SEC
        sleep(SLEEP_SEC)

    else:
      append_file(FAILURE_LIST, '%s %s' % (hash_actual, dir))

    if os.path.exists(archive_file):
      os.remove(archive_file)


def get_dirs_from_list(queue_file):
  entries = []
  with codecs.open(queue_file, 'r', 'utf-8') as f:
    try:
      for line in f:
        hash1, size, fmt, dir = re.split(r'\s+', line.strip(), 3)
        hash1 = str(hash1)
        if dir:
          if not os.path.exists(dir):
            print 'directory does not exist: %s' % dir
            raise Exception('directory does not exist: %s' % dir)
          entries.append((hash1, size, fmt, dir))
    except UnicodeDecodeError:
      raise Exception('Make sure "%s" is UTF-8' % queue_file)
  return entries


def main():
  SafeStreamFilter.substitute_stdout()

  target = sys.argv[1] if len(sys.argv) >= 2 else QUEUE_FILE
  assert os.path.exists(target)

  volume_dir = os.path.join(DB_ROOT, NAROD_VOLUME)
  if not os.path.exists(volume_dir):
    os.mkdir(volume_dir)

  empty_files(SUCCESS_LIST, FAILURE_LIST)

  if os.path.isdir(target):
    # upload single dir
    hash = None
    size = -1
    fmt = '?'
    dir = target.decode('1251')
    print dir
    assert os.path.exists(dir)
    entries = [ (hash, size, fmt, dir) ]
  else:
    # upload dirs from a list
    entries = get_dirs_from_list(target)

  for i, tuple in enumerate(entries):
    assert tuple
    hash1, size, fmt, dir = tuple
    print '--------------- Album %d/%d ----------------' % (i + 1, len(entries))
    print '%s (%s MB)' % (dir, size)

    last_iteration = i + 1 == len(entries)
    #print 'hash1 = ', hash1
    handle_dir(dir, hash1, last_iteration)

    sys.stdout.flush()

  print 'Finished. Press Enter'
  sys.stdout.flush()
  sys.stdin.readline()


if __name__ == '__main__':
  main()
