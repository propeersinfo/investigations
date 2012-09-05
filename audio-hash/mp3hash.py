# -*- coding: utf-8 -*-

import re
import traceback
import shutil
import win32api
import subprocess
import tempfile
import sys
import glob
import hashlib
import struct
import os
import math
from mutagen.id3 import ID3NoHeaderError
from mutagen.easyid3 import EasyID3
import time

from common import check_hex_digest, empty_files
from common import append_file

AUDIO_HASH_ID3_TAG = 'AUDIOHASH'
AUDIO_HASH_MUTAGEN_KEY = AUDIO_HASH_ID3_TAG.lower()

AUDIO_HASH_TIME_ID3_TAG = 'AUDIOHASHTIME'
AUDIO_HASH_TIME_MUTAGEN_KEY = AUDIO_HASH_TIME_ID3_TAG.lower()

EasyID3.RegisterTXXXKey(AUDIO_HASH_MUTAGEN_KEY, AUDIO_HASH_ID3_TAG)
EasyID3.RegisterTXXXKey(AUDIO_HASH_TIME_MUTAGEN_KEY, AUDIO_HASH_TIME_ID3_TAG)


def read_flac_audio_hash(file):
  assert os.path.exists(file)
  file_short = win32api.GetShortPathName(file)
  cmd = ['metaflac', '--show-md5sum', file_short]
  p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=None)
  p.wait()
  hash = p.stdout.read().strip().upper()
  return hash if check_hex_digest(hash) else None


def read_mp3_audio_hash_tag(mp3):
  def get_recheck_flag(audio):
    TIME_DIFFERENCE_TSHLD = 5 # in seconds; because writing tags to mp3 could take some time
    recheck = True
    try:
      time_tagged = audio[AUDIO_HASH_TIME_MUTAGEN_KEY][0]
    except KeyError:
      return True
      #print 'time_tagged: %s' % time_tagged
    if time_tagged:
      diff = os.path.getmtime(mp3) - float(time_tagged)
      #print 'time difference: %s' % diff
      if abs(diff) < TIME_DIFFERENCE_TSHLD:
        recheck = False
      #print 'recheck? %s' % recheck
    return recheck

  try:
    audio = EasyID3(mp3)
    hash = audio.get(AUDIO_HASH_MUTAGEN_KEY)
    if hash:
      return hash[0].upper(), get_recheck_flag(audio)
    else:
      return None, None
  except ID3NoHeaderError:
    return None, None


def write_mp3_audio_hash_tag(mp3, hash):
  try:
    audio = EasyID3(mp3)
  except ID3NoHeaderError:
    audio = EasyID3()
  audio[AUDIO_HASH_MUTAGEN_KEY] = hash
  audio[AUDIO_HASH_TIME_MUTAGEN_KEY] = str(time.time())
  audio.save(mp3)


def read_audio_data_hash_by_extension(file):
  ext = os.path.splitext(file)[1].lower()
  if ext == '.mp3':
    hash, recheck = read_mp3_audio_hash_tag(file)
    return hash
  elif ext == '.flac':
    return read_flac_audio_hash(file)
  else:
    return None


def get_mp3_audio_data(mp3_file):
  with open(mp3_file, 'rb') as f:
    buf = f.read()
  assert len(buf) == os.stat(mp3_file).st_size

  audio_start = 0
  audio_end = len(buf)

  if buf[0:3] == 'ID3':
    id3_v2_len = 20 if ord(buf[5]) & 0x10 else 10
    id3_v2_len += ((ord(buf[6]) * 128 + ord(buf[7])) * 128 + ord(buf[8])) * 128 + ord(buf[9])
    audio_start += id3_v2_len

  if buf[-128:-125] == 'TAG':
    audio_end -= 128

  ape_pos = buf.find('APETAGEX', audio_start, audio_end)
  if ape_pos >= 0:
    audio_end = ape_pos

  lyr = buf.find('LYRICSBEGIN', audio_start, audio_end)
  if lyr >= 0:
    audio_end = lyr

  # some taggers like Mutagen does place ID3v1 before APE
  # so let's try to recognize ID3v1 again
  p = audio_end - 128
  if p >= 0 and buf[p:p + 3] == 'TAG':
    audio_end = p

  return buf[audio_start:audio_end]


def calc_mp3_audio_hash(file):
  h = hashlib.md5()
  h.update(get_mp3_audio_data(file))
  return h.hexdigest().upper()


def calc_mp3_audio_hash_external_program(mp3_file, cmd_line_maker):
  mp3_file_short = win32api.GetShortPathName(mp3_file) # popen fails accepting unicode file names
  decoded_file = tempfile.NamedTemporaryFile(delete=False).name
  try:
    cmd = cmd_line_maker(decoded_file)
    #print 'cmd: %s' % cmd
    p = subprocess.Popen(cmd, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()

    assert os.path.exists(decoded_file)
    if os.stat(decoded_file).st_size > 0:
      with open(decoded_file, 'rb') as f:
        raw_mp3 = f.read()
      assert len(raw_mp3) == os.stat(decoded_file).st_size
      md5 = hashlib.md5()
      md5.update(raw_mp3)
      return md5.hexdigest().upper()
    else:
      return None
  finally:
    if os.path.exists(decoded_file):
      os.unlink(decoded_file)
      #shutil.move(decoded_file, '%s.mplayer' % mp3_file)


def calc_mp3_audio_hash_mplayer(mp3_file):
  def cmd_line_maker(out_file):
    MPLAYER = 'D:\\temp\\mpayer-cut\\MPlayer-rtm-svn-34401\\mplayer.exe'
    mp3_file_short = win32api.GetShortPathName(mp3_file) # popen fails accepting unicode file names
    return [MPLAYER, mp3_file_short, '-dumpaudio', '-dumpfile', out_file]

  return calc_mp3_audio_hash_external_program(mp3_file, cmd_line_maker)


# def calc_mp3_audio_hash_mpg123(mp3_file):
# 	def cmd_line_maker(out_file):
# 		EXE = 'D:\\portable\\extract_frames.exe'
# 		mp3_file_short = win32api.GetShortPathName(mp3_file) # popen fails accepting unicode file names
# 		return [ EXE, mp3_file_short,  out_file ]
# 	return calc_mp3_audio_hash_external_program(mp3_file, cmd_line_maker)


def calc_mp3_audio_hash_mpg123(mp3_file):
  #EXE = 'D:\\portable\\mp3hash.exe'
  EXE = 'mp3hash.exe'
  mp3_file = win32api.GetShortPathName(mp3_file)
  cmd = [EXE, mp3_file]
  p = subprocess.Popen(cmd, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  hash = p.communicate()[0]
  if p.returncode == 0:
    assert check_hex_digest(hash)
    return hash
  else:
    return None


# def main_update_files():
# 	SafeStreamFilter.substitute_stdout()

# 	def do_mp3(mp3):
# 		# write the tag
# 		h = calc_mp3_audio_hash(mp3)
# 		print 'setting %s %s' % (h, mp3)
# 		write_audio_hash_tag(mp3, h)
# 		# a little self-test
# 		h2 = calc_mp3_audio_hash(mp3)
# 		assert h == h2, '%s vs %s' % (h, h2)

# 	target = sys.argv[2]
# 	if os.path.isfile(target):
# 		do_mp3(target)
# 	elif os.path.isdir(target):
# 		for dir, subdirs, subfiles in os.walk(unicode(target)):
# 			for file in glob.glob1(dir, '*.mp3'):
# 				do_mp3(os.path.join(dir, file))


# def main_self_test_against_mp3tag():
# 	SafeStreamFilter.substitute_stdout()
# 	from common import collect_audio_hashes
# 	root_dir = sys.argv[2]
# 	golden_db = collect_audio_hashes(sys.argv[3])
# 	#root_dir = 'D:\\downloads\\sync\\via'
# 	#root_dir = u'D:\\downloads\\sync\\via\\Аккорд\\Аккорд - Хлоп-хлоп LP [33Д-028605] 1970'
# 	#root_dir = u'D:\\downloads\\sync\\via\\Весёлые ребята\\VIA VESELIUE REBJATA-DISKI GIGANTIU VINIL [LP]\\VIA VESELIUE REBJATA-1980-Diskoklub-2-С60-16109-10 [LP]'
# 	#root_dir = u'D:\\downloads\\sync\\via\\Гая\\Гая - Озорная тучка EP [Д-00028671-72] 1970'
# 	#root_dir = u'D:\\downloads\\sync\\via\\Самоцветы'
# 	cnt = 0
# 	LOG = '%s.log' % sys.argv[0]
# 	append_file(LOG, '-----------------------------')
# 	for dir, subdirs, subfiles in os.walk(unicode(root_dir)):
# 		for file in glob.glob1(dir, u'*.mp3'):
# 			try:
# 				cnt += 1
# 				if cnt % 50 == 0:
# 					sys.stdout.write(' %.1f%%' % (float(cnt)/len(golden_db)*100))
# 				file = os.path.join(dir, file)
# 				h1 = calc_mp3_audio_hash(file)
# 				h2 = golden_db.get(file)
# 				if h1 != h2:
# 					print 'failed for %s' % file
# 					print '-> %s vs %s' % (h1, h2)
# 					append_file(LOG, '%s: %s vs %s' % (file, h1, h2))
# 			except BaseException, msg:
# 				print 'exception: %s' % msg
# 				append_file(LOG, 'exception: %s' % msg)


# def main_self_test_against_external_programs():
# 	SafeStreamFilter.substitute_stdout()

# 	LOG = '~main_self_test_against_mplayer.log'

# 	#root_dir = 'D:\\downloads\\sync'
# 	root_dir = sys.argv[2]

# 	cnt = 0
# 	append_file(LOG, '-----------------------------')
# 	for dir, subdirs, subfiles in os.walk(unicode(root_dir)):
# 		for file in glob.glob1(dir, u'*.mp3'):
# 			try:
# 				cnt += 1
# 				if cnt % 10 == 0:
# 					sys.stdout.write(' %s' % (cnt))

# 				file = os.path.join(dir, file)
# 				#h1 = calc_mp3_audio_hash(file)
# 				h2 = calc_mp3_audio_hash_mplayer(file)
# 				h3 = calc_mp3_audio_hash_mpg123(file)
# 				if not (h2 == h3):
# 					#print 'failed for %s' % file
# 					#print '-> %s vs %s vs %s' % (h1, h2, h3)
# 					append_file(LOG, u'%s: %s vs %s' % (win32api.GetShortPathName(file), h2, h3))
# 			except KeyboardInterrupt:
# 				return
# 			except BaseException, msg:
# 				print 'exception: %s' % msg
# 				append_file(LOG, 'exception: %s' % msg)
# 				append_file(LOG, '  file: %s' % file)
# 				with open('log', 'a+') as log:
# 					traceback.print_exc(file=log)


def main_update():
  ''' update given mp3's with md5 of their audio content '''

  ERROR_LOG = '~errors.m3u'
  BADMP3_LOG = '~incorrect.m3u'
  GENERAL_LOG = '~general.log'
  # FORCE_REWRITE = True

  # if FORCE_REWRITE:
  # 	print "warning: FORCE_REWRITE is on"
  # 	append_file(ERROR_LOG, "warning: FORCE_REWRITE is on")

  root_dir = sys.argv[2]

  def do_mp3(file):
    append_file(GENERAL_LOG, 'File %s ...' % file)
    h_tag, recheck = read_mp3_audio_hash_tag(file)
    do_write = True
    if h_tag:
      do_write = False
      if not check_hex_digest(h_tag):
        append_file(ERROR_LOG, 'ERROR: invalid hash %s stored in file %s' % (h_tag, file))
      elif recheck:
        do_write = True
    if do_write:
      h_123 = calc_mp3_audio_hash_mpg123(file)
      if h_123:
        assert check_hex_digest(h_123)
        tmp = tempfile.NamedTemporaryFile(delete=False).name
        try:
          # mp3 tagging is dangerous so do a test write first
          shutil.copy(file, tmp)
          write_mp3_audio_hash_tag(tmp, h_123)

          h_re = calc_mp3_audio_hash_mpg123(tmp)
          if h_re == h_123:
            write_mp3_audio_hash_tag(file, h_123)
          else:
            append_file(ERROR_LOG,
              u'# ERROR: file got different hash sum after tagging! Original file not affected: %s' % file)
            append_file(ERROR_LOG, win32api.GetShortPathName(file))
        finally:
          if os.path.exists(tmp):
            os.remove(tmp)
      else:
        append_file(BADMP3_LOG, "# %s" % file)
        append_file(BADMP3_LOG, win32api.GetShortPathName(file))

  empty_files(ERROR_LOG, BADMP3_LOG, GENERAL_LOG)
  #append_file(ERROR_LOG,  '#-----------------------------')
  #append_file(BADMP3_LOG, '#-----------------------------')
  #append_file(GENERAL_LOG, '#-----------------------------')

  def collect_mp3s(root_dir):
    files = []
    for dir, subdirs, subfiles in os.walk(unicode(root_dir)):
      for file in glob.glob1(dir, u'*.mp3'):
        files.append(os.path.join(dir, file))
    return files

  print 'collecting mp3 names...'
  files = collect_mp3s(root_dir)
  print '%d mp3 files at all' % len(files)
  for cnt, file in enumerate(files):
    try:
      if cnt % 20 == 0:
        pct = float(cnt) / len(files) * 100
        sys.stdout.write('%.1f%%' % pct)
      else:
        sys.stdout.write('.')

      if os.path.exists(file):
        # file may disappear after its name has been collected
        do_mp3(file)

    except KeyboardInterrupt:
      print >> sys.stderr, 'KeyboardInterrupt happened'
      return
    except BaseException, msg:
      print >> sys.stderr, 'exception: %s' % msg
      append_file(ERROR_LOG, '# exception: %s' % msg)
      append_file(ERROR_LOG, '# %s' % file)
      append_file(ERROR_LOG, win32api.GetShortPathName(file))
      with open(GENERAL_LOG, 'a+') as log:
        traceback.print_exc(file=log)


def main_show_hash():
  #SafeStreamFilter.substitute_stdout()
  target = sys.argv[2]

  total = [0]
  hashed = [0]
  recheckable = [0]

  def do_mp3(mp3):
    tagged_hash, recheck = read_mp3_audio_hash_tag(mp3)
    recheck_str = 'RE' if recheck else 'ok'
    print '%s %s %s' % (tagged_hash, recheck_str, mp3)
    total[0] += 1
    if tagged_hash:
      hashed[0] += 1
      if recheck: recheckable[0] += 1

  if os.path.isfile(target):
    do_mp3(target)
  elif os.path.isdir(target):
    for dir, subdirs, subfiles in os.walk(unicode(target)):
      for file in glob.glob1(dir, u'*.mp3'):
        do_mp3(os.path.join(dir, file))

  print 'total=%d hashed=%s recheck=%s' % (total[0], hashed[0], recheckable[0])


def main_check_tag():
  ''' check if hash value written to the tag matches actual hash '''

  #SafeStreamFilter.substitute_stdout()
  target = sys.argv[2]

  def do_mp3(mp3):
    status = '?'
    recheck_str = None
    try:
      h_tag, recheck = read_mp3_audio_hash_tag(mp3)
      recheck_str = 'RE' if recheck else 'ok'
      if not h_tag:
        return None
      h_tag = h_tag.upper()
      h_123 = calc_mp3_audio_hash_mpg123(mp3)
      if not h_123:
        return None
      assert check_hex_digest(h_tag)
      assert check_hex_digest(h_123)
      eq = (h_tag == h_123)
      status = 'eq' if eq else 'NE'
      return eq
    finally:
      print '%-2s %2s %s' % (status, recheck_str, win32api.GetShortPathName(mp3))

  class Stat:
    def __init__(self):
      self.cnt_total = 0
      self.cnt_eq = 0
      self.cnt_ne = 0

  def upd_stat(stat, ret_val):
    if ret_val is not None:
      if ret_val:
        stat.cnt_eq += 1
      else:
        stat.cnt_ne += 1
    stat.cnt_total += 1

  stat = Stat()
  if os.path.isfile(target):
    upd_stat(stat, do_mp3(target))
  elif os.path.isdir(target):
    for dir, subdirs, subfiles in os.walk(unicode(target)):
      for file in glob.glob1(dir, u'*.mp3'):
        upd_stat(stat, do_mp3(os.path.join(dir, file)))

  print 'total=%d passed=%d failed=%d none=%d' % (
  stat.cnt_total, stat.cnt_eq, stat.cnt_ne, (stat.cnt_total - stat.cnt_eq - stat.cnt_ne))


def main_strip_tags():
  mp3 = sys.argv[2]
  size1 = os.stat(mp3).st_size
  data = get_mp3_audio_data(mp3)
  with open(mp3, 'wb') as f:
    f.write(data)
  size2 = os.stat(mp3).st_size
  print 'tags stripped from %d to %d' % (size1, size2)


def main_info():
  mp3 = sys.argv[2]
  print 'info for %s:' % mp3
  with open(mp3, 'rb') as f:
    buf = f.read()
  assert len(buf) == os.stat(mp3).st_size
  print 'length: %s' % len(buf)
  v1 = buf.rfind('TAG')
  if v1 >= 0:
    print 'TAG\' position: %s (%s)' % (v1, len(buf) - v1)
    print '128 bytes: %s' % len(buf[v1:len(buf)])


if __name__ == '__main__':
  actions = {
    #'test_mp3tag':   main_self_test_against_mp3tag,
    #'test_external':  main_self_test_against_external_programs,
    'update': main_update,
    #'update': main_update_files,
    'show': main_show_hash,
    'strip': main_strip_tags,
    'debug': main_info,
    'check': main_check_tag,
    }
  actions[sys.argv[1]]()
