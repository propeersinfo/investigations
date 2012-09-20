# -*- coding: utf-8 -*-

import json
import re
import os
import zipfile
import glob
import codecs
import hashlib
import Image
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from utils import pretty_print_json_as_readable_unicode, dict_of_lists

MIN_FILES_IN_ALBUM = 2
RECOGNIZED_AUDIO_EXTENSIONS = [ 'mp3', 'flac', 'ape' ]
ALLOWED_AUDIO_EXTENSIONS    = [ 'mp3', 'flac' ]


def tempfilename():
  from tempfile import NamedTemporaryFile
  return NamedTemporaryFile(delete=False).name


def list_multiple_lists(list1, list2):
  assert len(list1) == len(list2)
  for i,elem1 in enumerate(list1):
    yield elem1, list2[i]


def check_hex_digest(hex_str):
  return not not re.match('^[0-9A-Fa-f]{32}$', hex_str)


def listdir(dir):
  assert os.path.exists(dir), dir
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
  MIXED_CODECS = Cause("MC")
  HASH_MISSED = Cause("HM")
  ILLEGAL_HASH = Cause("IH")
  def __init__(self, code, dir, msg = None):
    super(Exception, self).__init__('%s for %s ' % (msg, dir))
    self.code = code
    self.dir = dir
    self.msg = msg


def get_audio_files(dir):
  assert os.path.exists(dir)
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


def check_files_continuosity(dir, files):
  """ it is expected param 'files' is sorted already """
  REGEX_01  = '^([0-9][0-9]?)[^0-9].+' # 1, 01
  REGEX_101 = '^([0-9])([0-9][0-9])[ -_.].+' # 101, 102, 201, 202
  REGEX_A1  = '^([a-dA-D])([0-9]{1,2})[ -_.].+'
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
  elif re.search(REGEX_101, files[0]):
    cur_dsc = 0
    cur_trk = 0
    for i,file in enumerate(files):
      m = re.search(REGEX_101, file)
      if m:
        dsc = int(m.group(1))
        trk = int(m.group(2))
        #print 'track %s %s' % (dsc, trk)
        if dsc != cur_dsc:
          if dsc != cur_dsc + 1:
            raise NotAlbumException(NotAlbumException.NOT_CONTINUOUS, dir, '(5) %s%s' % (dsc,trk))
          cur_dsc = dsc
          cur_trk = 0
          #print 'rewritten to: %s %s' % (dsc, trk)
        if trk != cur_trk + 1:
          raise NotAlbumException(NotAlbumException.NOT_CONTINUOUS, dir, '(6) files are not continuous: %s and %s' % (cur_trk, trk))
        cur_trk += 1
      else:
        raise NotAlbumException(NotAlbumException.NOT_CONTINUOUS, dir, '(4) files are not continuous')
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
            raise NotAlbumException(NotAlbumException.NOT_CONTINUOUS, dir, '(1) %s%s' % (m.group(1), m.group(2)))
          cur_chr = chr
          cur_dig = 0
        # check the number part
        if dig != cur_dig + 1:
          raise NotAlbumException(NotAlbumException.NOT_CONTINUOUS, dir, '(2) %s%s' % (m.group(1), m.group(2)))
        cur_dig += 1
      else:
        raise NotAlbumException(NotAlbumException.NOT_CONTINUOUS, dir, '(3) files are not continuous')
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


class Album(dict):
  def get_audio_format(self):
    """
    Actually return extension of the first file.
    It is assumed every file in an album has the same extension.
    """
    if len(self['tracks']) > 0:
      a_fname = self['tracks'][0]['file_name']
      return os.path.splitext(a_fname)[1][1:].upper()
    else:
      return None


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
  if len(files_short) <= 0:
    raise NotAlbumException(NotAlbumException.NO_AUDIO_FILES, dir)
  check_files_continuosity(dir, files_short)
  #print "dir: %s" % dir
  dir_size, audio_size = get_album_sizes(dir)
  ah = hashlib.md5()
  album = Album({
    #'album_hash': ah,
    'path': dir,
    'total_size': dir_size,
    'audio_size': audio_size,
    })
  album['tracks'] = []
  for file_short in files_short:
    file_full = os.path.join(dir, file_short)
    one_hash = hash_db.get(file_full)
    if not one_hash:
      raise NotAlbumException(NotAlbumException.HASH_MISSED, dir)
    if not check_hex_digest(one_hash):
      raise NotAlbumException(NotAlbumException.ILLEGAL_HASH, dir)
    ah.update(one_hash)
    track = {'file_name': file_short,
             'audio_hash': hash_db[file_full],
             'file_size': os.stat(file_full).st_size, }
    track = dict(track.items() + get_media_info(file_full).items())
    album['tracks'].append(track)
  album['album_hash'] = ah.hexdigest().upper()
  return album


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
      album['ctime'] = os.path.getctime(fl)
      yield album


def load_db_volumes(db_root, *volume_names):
  volume_objects = []
  albums_by_hash = dict_of_lists()

  if not volume_names:
    volume_names = [ name for name in os.listdir(db_root) ]

  #assert len(volume_names) > 0
  #assert isinstance(volume_names[0], basestring)

  for volume_name in volume_names:
    volume_dir = os.path.join(db_root, volume_name)
    if not os.path.isdir(volume_dir):
      continue
    volume = {
      'name': volume_name,
      'entries': {}
    }
    volume_objects.append(volume)
    for album_json_short in os.listdir(volume_dir):
      if check_hex_digest(album_json_short):
        album_json_long = os.path.join(volume_dir, album_json_short)
        album_obj = json.loads(read_file(album_json_long))
        ah = album_obj['album_hash']
        assert ah == album_json_short, '%s vs %s' % (ah, album_json_short)
        volume['entries'][ah] = album_obj
        albums_by_hash.append(ah, album_obj)
  return volume_objects, albums_by_hash


def save_db_album(db_root, volume_name, album, suffix=None):
  assert album['album_hash']
  assert len(album['tracks'])

  json_file_tmp = tempfilename()
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
  json.loads(read_file(json_file_real))


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


class CoverImage:
  def __init__(self, dir, file_short):
    self.dir = dir
    self.file_short = file_short
    self.image = Image.open(os.path.join(dir, file_short))
  def is_quad(self):
    ratio = float(self.image.size[0]) / self.image.size[1]
    diff = abs(1.0 - ratio)
    return diff < 0.1
  def resize(self, side_size):
    w, h = self.image.size
    if w != side_size or h != side_size:
      self.image = self.image.resize((side_size,side_size), Image.ANTIALIAS)
  def save(self, dir, base_name):
    assert os.path.isdir(dir), dir
    fname = os.path.join(dir, '%s.jpg' % base_name)
    self.image.save(fname)
  def exists_at(self, dir, base_name):
    fname = os.path.join(dir, '%s.jpg' % base_name)
    return os.path.exists(fname)


def find_cover_image(dir):
  # collect
  images = []
  for ext in [ 'jpg', 'jpeg', 'png', 'bmp' ]:
    images += [ CoverImage(dir, short_name) for short_name in glob.glob1(dir, '*.%s' % ext) ]

  images = sorted(images, key=lambda img: img.file_short.lower())

  # filter those looking like covers
  images = filter(lambda img: img.is_quad(), images)

  # order by file name
  order = [ 'front', 'cover', 'folder', 'side', 'rear', 'back' ]
  for pattern in order:
    for img in images:
      pattern = '.*%s.*' % pattern
      if re.search(pattern, img.file_short, re.I):
        return img

  return images[0] if len(images) else None # any
