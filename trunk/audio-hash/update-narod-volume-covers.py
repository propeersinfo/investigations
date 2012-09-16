import os
import win32api
import common

DB_ROOT = 'DB'
NAROD_VOLUME = 'narod'
COVER_DIR = os.path.join('covers', 'all')
COVER_SIZE = 200

dir = os.path.join(DB_ROOT, NAROD_VOLUME)
for album in common.list_db_volume(unicode(dir)):
  if os.path.isdir(album['path']):
    #  and album['album_hash'] == 'E137690D9B7845BBE4B870213D85C8BC'
    print win32api.GetShortPathName(album['path'])
    cover = common.find_cover_image(album['path'])
    if cover:
      if not cover.exists_at(COVER_DIR, album['album_hash']):
        cover.resize(COVER_SIZE)
        cover.save(COVER_DIR, album['album_hash'])