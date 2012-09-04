# -*- coding: utf-8 -*-

import json
import sys
import re
import os
import zipfile
import glob
import codecs
import hashlib
from StringIO import StringIO
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from utils import pretty_print_json_as_readable_unicode

MIN_FILES_IN_ALBUM = 2
RECOGNIZED_AUDIO_EXTENSIONS = [ 'mp3', 'flac', 'ape' ]
ALLOWED_AUDIO_EXTENSIONS    = [ 'mp3', 'flac' ]


def tmpfile():
  from tempfile import NamedTemporaryFile
  return NamedTemporaryFile(delete=False).name


def list_multiple_lists(list1, list2):
  assert len(list1) == len(list2)
  for i,elem1 in enumerate(list1):
    yield elem1, list2[i]


def check_hex_digest(hex_str):
  return not not re.match('^[0-9A-Fa-f]{32}$', hex_str)


def listdir(dir):
  for file in os.listdir(dir):
    yield file, os.path.join(dir, file)


def append_file(file, content):
  with codecs.open(file, 'a+', 'utf-8') as f:
    if content == '':
      f.write(content)
    else:
      print >> f, content


def write_file(file, content):
  with codecs.open(file, 'w', 'utf-8') as f:
    f.write(content)


def empty_files(*files):
  for file in files:
    write_file(file, '')


def read_file(file):
  with codecs.open(file, 'r', 'utf-8') as f:
    return f.read()


# try to cut off the given start of the string
# case insensitive
def cut_start(title, pattern):
  if title.lower().find(pattern) == 0:
    title = title[len(pattern):]
  return title


class AudioHashFromFileDictionary(dict):
  def __getitem__(self, key):
    return self.get(key)

  def get(self, file_name, default=None):
    assert default == None
    import mp3hash

    hash = mp3hash.read_audio_data_hash_by_extension(file_name)
    #print 'returning %s' % hash
    return hash

  def __contains__(self, key):
    raise Exception('is not implemented yet')

  def has_key(self, key):
    raise Exception('is not implemented yet')


def collect_audio_hashes():
  return AudioHashFromFileDictionary()


class NotAlbumException(Exception):
  class Cause:
    def __init__(self, name, serious=True):
      self.name = name
      self.serious = serious
    def __str__(self):
      return self.name
  NO_AUDIO_FILES = Cause("NA", False)
  NOT_CONTINUOUS = Cause("NC")
  COUNTER_FAILED = Cause("CF")
  A1_NOT_IMPLEMENTED = Cause("A1")
  UNKNOWN_PATTERN = Cause("UP")
  AUDIO_FORMAT = Cause("AF")
  MIN_FILES = Cause("MF")
  def __init__(self, code, dir, msg = None):
    super(Exception, self).__init__('%s for %s ' % (msg, dir))
    self.code = code
    self.dir = dir
    self.msg = msg


def get_audio_files(dir):
  files_by_ext = {}
  for ext in RECOGNIZED_AUDIO_EXTENSIONS:
    mask = '*.%s' % ext
    files = [file for file in glob.glob1(dir, mask)]
    if len(files) > 0:
      files_by_ext[ext] = files

  if len(files_by_ext) == 0:
    raise NotAlbumException(NotAlbumException.NO_AUDIO_FILES, dir)
  elif len(files_by_ext) == 1:
    ext = files_by_ext.keys()[0]
    if ext.lower() not in ALLOWED_AUDIO_EXTENSIONS:
      raise NotAlbumException(NotAlbumException.AUDIO_FORMAT, dir, "extension=%s" % ext)
    files = files_by_ext.values()[0]
    if len(files) >= MIN_FILES_IN_ALBUM:
      return sorted(files), ext
    else:
      raise NotAlbumException(NotAlbumException.MIN_FILES, dir, "files=%d" % len(files))
  else:
    raise NotAlbumException(NotAlbumException.MIXED_CODECS, dir)


# def get_album_format(dir):
# 	print 'dir is ', dir
# 	_, ext = get_audio_files(dir)
# 	return ext.upper()


def check_files_continuosity(dir, files):
  ''' it is expected param 'files' is sorted already '''
  REGEX_01 = '^([0-9]{1,2})[ -_.].+'
  REGEX_A1 = '^([a-dA-D])([0-9]{1,2})[ -_.].+'
  assert len(files) > 0
  if re.search(REGEX_01, files[0]):
    cnt = 1
    for file in files:
      m = re.search(REGEX_01, file)
      if m:
        pos = int(m.group(1))
        if pos != cnt:
          raise NotAlbumException(NotAlbumException.COUNTER_FAILED, dir, 'files are not continuous: %d->%d' % (cnt-1, pos))
        cnt += 1
      else:
        raise NotAlbumException(NotAlbumException.NOT_CONTINUOUS, dir, 'files are not continuous')
  elif re.search(REGEX_A1, files[0]):
    cur_chr = ord('A')
    cur_dig = 0
    for i,file in enumerate(files):
      m = re.search(REGEX_A1, file)
      if m:
        chr = ord(m.group(1).upper())
        dig = int(m.group(2))
        # check character pater
        if chr != cur_chr:
          if chr != cur_chr + 1:
            raise NotAlbumException(NotAlbumException.NOT_CONTINUOUS, dir, '%s%s' % (m.group(1), m.group(2)))
          cur_chr = chr
          cur_dig = 0
        # check the number part
        if dig != cur_dig + 1:
          raise NotAlbumException(NotAlbumException.NOT_CONTINUOUS, dir, '%s%s' % (m.group(1), m.group(2)))
        cur_dig += 1
      else:
        raise NotAlbumException(NotAlbumException.NOT_CONTINUOUS, dir, 'files are not continuous')
  else:
    start = files[0][0:10]
    raise NotAlbumException(NotAlbumException.UNKNOWN_PATTERN, dir, u'unknown file pattern "%s"' % start)


def archive_dir(dir, arc_name):
  ''' archive a directory's files
      no sub directories
      no compression
  '''
  assert type(dir) == unicode
  assert os.path.isdir(dir)

  dir_short = os.path.split(dir)[1]

  if os.path.exists(arc_name):
    assert os.path.isfile(arc_name)
    os.remove(arc_name)

  zf = zipfile.ZipFile(arc_name, mode='w')
  for file_short in os.listdir(dir):
    file_full = os.path.join(dir, file_short)
    if os.path.isfile(file_full):
      zf.write(file_full, arcname=u'%s/%s' % (dir_short, file_short))
  zf.close()


#def diff(a, b, path='/root'):
#  ka = set(a.keys())
#  kb = set(b.keys())
#  if ka != kb:
#    diff1 = ka - kb
#    diff2 = kb - ka
#    print '%s' % path
#    for key in diff1:
#      print '< %s => ...' % key
#    for key in diff2:
#      print '> %s => ...' % key
#  else:
#    for key in ka:
#      val_a = a[key]
#      val_b = b[key]
#      if type(val_a) == type(val_b):
#        if type(val_a) == dict:
#          diff(val_a, val_b, '%s/%s' % (path, key))
#        elif val_a != val_b:
#          print '%s' % path
#          print '< %s => %s' % (key, val_a)
#          print '> %s => %s' % (key, val_b)
#      else:
#        print '%s' % path
#        print '< %s => %s' % (key, type(val_a))
#        print '> %s => %s' % (key, type(val_b))

class Album(dict):
  def get_audio_format(self):
    '''
    Actually return extension of the first file.
    It is assumed every file in an album has the same extension.
    '''
    if len(self['tracks']) > 0:
      a_fname = self['tracks'][0]['file_name']
      return os.path.splitext(a_fname)[1][1:].upper()
    else:
      return None
#  def __eq__(self, other):
#    assert type(other) == Album
#    d1 = json.loads(json.dumps(self))
#    d2 = json.loads(json.dumps(other))
#
##    write_file('cmp.self', json.dumps(self))
##    write_file('cmp.other', json.dumps(other))
#
#    eq = d1 == d2
#    return eq
#    #return False


def __calc_album_hash(hash_db, dir, afiles_short, warnings=None):
  def warn(msg):
    if warnings:
      print >> warnings, msg

  # if afiles_short == None:
  # 	afiles_short = get_audio_files(dir)

  ah = hashlib.md5()
  for i, file in enumerate(afiles_short):
    assert isinstance(dir, basestring)
    assert isinstance(file, basestring), 'actual type %s' % type(file)
    file_abs = os.path.join(dir, file)
    #print file_abs
    one_hash = hash_db.get(file_abs)
    if not one_hash:
      warn(u'audio hash not found for files[%d] in %s' % (i, dir))
      return None
    one_hash = one_hash.upper()
    #assert len(one_hash) == 32, 'Bad hash %s' % one_hash
    assert check_hex_digest(one_hash), 'Bad hash %s' % one_hash
    #assert int(one_hash,16) != 0, Exception(u'bad hash %s for file %s' % (one_hash, file_abs))
    if int(one_hash, 16) == 0:
      # this may happen for wma, ogg or 24 bit flac encoded by foobar2000
      warn('zero audio hash in %s' % dir)
      return None
    ah.update(one_hash)
  return ah.hexdigest().upper()


def get_media_info(file):
  ext = os.path.splitext(file)[1][1:].lower()
  if ext == 'mp3':
    audio = MP3(file)
    return {
      'bit_rate': audio.info.bitrate / 1000,
      'sample_rate': audio.info.sample_rate,
      'length': audio.info.length,
      }
  elif ext == 'flac':
    audio = FLAC(file)
    return {
      #'bit_rate': audio.info.bitrate / 1000, # N/A for flac in mutagen
      'bits_per_sample': audio.info.bits_per_sample,
      'sample_rate': audio.info.sample_rate,
      'length': audio.info.length,
    }
  else:
    return {}


def scan_album_from_dir(dir):
  assert type(dir) == unicode
  hash_db = collect_audio_hashes()
  files_short, ext = get_audio_files(dir)
  if files_short:
    check_files_continuosity(dir, files_short)
    ah = __calc_album_hash(hash_db, dir, files_short)
    assert ah is not None
    if ah:
      dir_size, audio_size = get_album_sizes(dir)
      album = Album({
        'album_hash': ah,
        'path': dir,
        'total_size': dir_size,
        'audio_size': audio_size,
        })
      album['tracks'] = []
      for file_short in files_short:
        file_full = os.path.join(dir, file_short)
        track = {'file_name': file_short,
                 'audio_hash': hash_db[file_full],
                 'file_size': os.stat(file_full).st_size, }
        track = dict(track.items() + get_media_info(file_full).items())
        album['tracks'].append(track)
      return album
  return None


def calc_album_hash(dir):
  album = scan_album_from_dir(dir)
  return album['album_hash'] if album else None


def list_db_volume(dir):
  for fs,fl in listdir(dir):
    if check_hex_digest(fs):
      with codecs.open(fl, 'r', 'utf-8') as f:
        json_text = f.read()
      json_obj = json.loads(json_text)
      album = Album(json_obj)
      yield album


def save_db_album(db_root, volume_name, album, suffix=None):
  assert album['album_hash']
  assert len(album['tracks'])

  json_file_tmp = tmpfile()
  json_file_real = os.path.join(db_root, volume_name, album['album_hash'])
  if suffix:
    json_file_real = '%s.%s' % (json_file_real, suffix)

  #json_text = json.dumps(album, indent=2)
  json_text = pretty_print_json_as_readable_unicode(album)
  write_file(json_file_tmp, json_text)

  # make sure it could be parsed back
  json.loads(read_file(json_file_tmp))

  if os.path.exists(json_file_real):
    os.remove(json_file_real)
  assert os.path.exists(json_file_tmp)
  assert not os.path.exists(json_file_real)
  os.rename(json_file_tmp, json_file_real)

  # make sure it could be parsed back
  with codecs.open(json_file_real, 'r', 'utf-8') as f:
    json.loads(f.read())


def get_album_sizes(dir):
  total_sz = 0
  audio_sz = 0
  for file_short in os.listdir(dir):
    file_long = os.path.join(dir, file_short)
    if os.path.isfile(file_long):
      info = os.stat(file_long)

      ext = os.path.splitext(file_long)[1][1:].lower()
      if ext in RECOGNIZED_AUDIO_EXTENSIONS:
        audio_sz += info.st_size

      total_sz += info.st_size

  return total_sz, audio_sz


