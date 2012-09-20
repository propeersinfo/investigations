# -*- coding: utf-8 -*-

import subprocess
import os
import sys
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
import glob
import win32api

from common import tempfilename
import common
from utils import format_time_hms

SOX = 'sox.exe'
AUDIO_FILES_MAX = 5
PREVIEW_DIR = 'previews'
TARGET_EXT = 'ogg'

DB_ROOT = 'DB'
NAROD_VOLUME = 'narod'
COVER_DIR = os.path.join('covers', 'all')


class SoxException(Exception):
  pass


def _get_audio_length(audio_file):
  ext = os.path.splitext(audio_file)[1].lower()
  return {
    '.mp3': lambda file: MP3(audio_file).info.length,
    '.flac': lambda file: FLAC(audio_file).info.length,
  }[ext](audio_file)


def _get_preview_range(total_length):
  """ get a piece from the middle """
  PREVIEW_LENGTH = 20
  start = float(total_length) / 2 - float(PREVIEW_LENGTH) / 2
  if start < 0:
    start = 0
  cut_len = PREVIEW_LENGTH
  return start, cut_len


def _concat_audio_files_for_preview(audio_files, dest_file):
  assert len(audio_files) > 0

  ext = os.path.splitext(dest_file)[1].lower()
  sample_rate = { '.mp3': 32000, '.ogg': 24000 }[ext]

  cmd = [ SOX, '--norm=0', ]
  for cut_file in audio_files:
    cmd.append(cut_file)
  cmd.append('-r')
  cmd.append(str(sample_rate))
  cmd.append(dest_file)
  cmd.append('remix') # mono
  cmd.append('-')
  p = subprocess.Popen(cmd)
  p.wait()
  if p.returncode != 0:
    raise SoxException('cannot concat audio cuts')


def _make_preview_single_audio(file_long):
  cut_file = tempfilename()
  if os.path.exists(cut_file):
    os.remove(cut_file)
  cut_file = '%s.wav' % cut_file
  track_len = _get_audio_length(file_long)
  start, len = _get_preview_range(track_len)
  start_hms = format_time_hms(start)
  len_hms = format_time_hms(len)
  #print '------------'
  #print '%s' % file_long
  #print '%s' % cut_file
  #print 'length=%s from %s to %s' % (track_len, start_hms, len_hms)
  #file_param = file_long.encode(sys.getfilesystemencoding())
  file_param = win32api.GetShortPathName(file_long)
  cmd = [SOX, file_param, cut_file, 'trim', start_hms, len_hms]
  #print cmd
  #if True: raise 'breakkk'
  p = subprocess.Popen(cmd)
  p.wait()
  if p.returncode == 0:
    return cut_file
  else:
    raise SoxException('sox has exited with code %s' % p.returncode)


def make_album_preview(dir, dest):
  dir = unicode(dir)
  assert os.path.isdir(dir)

  cut_files = []

  try:
    src_files = []
    src_files += glob.glob1(dir, u'*.mp3')
    src_files += glob.glob1(dir, u'*.flac')
    src_files = src_files[:AUDIO_FILES_MAX]
    for file_short in src_files:
      file_long = os.path.join(dir, file_short)
      cut_file = _make_preview_single_audio(file_long)
      cut_files.append(cut_file)

    print 'concatenating to %s' % dest
    _concat_audio_files_for_preview(cut_files, dest)
  finally:
    for cut_file in cut_files:
      if os.path.exists(cut_file):
        os.remove(cut_file)

def find_albums():
  found = []
  root = os.path.join(DB_ROOT, NAROD_VOLUME)
  for album in common.list_db_volume(unicode(root)):
    if os.path.isdir(album['path']):
      dir = album['path']
      dir_short = win32api.GetShortPathName(dir)
      #print dir_short
      preview_file = os.path.join(PREVIEW_DIR, '%s.%s'% (album['album_hash'], TARGET_EXT))
      if not os.path.exists(preview_file) and os.path.exists(dir):
        found.append(album)
  return found

albums = find_albums()
for i,album in enumerate(albums):
  dir = album['path']
  dir_short = win32api.GetShortPathName(dir)
  print '--------- album %d/%d ---------' % (i+1, len(albums))
  print dir_short
  assert os.path.exists(dir)
  preview_file = os.path.join(PREVIEW_DIR, '%s.%s'% (album['album_hash'], TARGET_EXT))
  try:
    make_album_preview(dir, preview_file)
  except SoxException, e:
    print 'failed to make audio preview'
