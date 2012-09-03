# -*- coding: utf-8 -*-

import sys
import json
import re
import os
import glob
import codecs
import hashlib

from common import collect_audio_hashes
from common import get_audio_files
from common import TrackContinuosityError
from common import calc_album_hash
from common import check_files_continuosity
from common import scan_album_dir
from common import save_db_album
from common import SafeStreamFilter

DB_ROOT = '.\\DB'


def init_db_volume(db_root, volume_name):
    ''' remove every regular file in the given directory '''
    dir = os.path.join(db_root, volume_name)

    if not os.path.exists(dir):
        os.mkdir(dir)

    for file_short in glob.glob1(dir, '*'):
        file_abs = os.path.join(dir, file_short)
        if os.path.exists(file_abs) and os.path.isfile(file_abs):
            os.remove(file_abs)


if __name__ == '__main__':
    SafeStreamFilter.substitute_stdout()

    assert len(sys.argv) >= 3
    root_dir = sys.argv[1]
    volume_name = sys.argv[2]

    if type(root_dir) == str:
        print 'decoding...'
        root_dir = root_dir.decode('windows-1251') # todo: how to rewrite that in a general way?

    assert os.path.exists(root_dir) and os.path.isdir(root_dir)

    hash_db = collect_audio_hashes()

    init_db_volume(DB_ROOT, volume_name)

    warnings = None
    #warnings = sys.stdout # enable it to see warnings instead of recognized albums

    album_cnt = 0
    for dir, subdirs, subfiles in os.walk(unicode(root_dir)):
        album = scan_album_dir(dir, hash_db, warnings=warnings)
        if album:
            album_cnt += 1
            #print u'album detected: %s' % dir
            if not warnings:
                print u'%s %s' % (album['album_hash'], dir)
            save_db_album(DB_ROOT, volume_name, album)
        else:
            #print u'not an album: %s' % dir
            pass

    print 'volume %s updated' % volume_name
    print '%d albums found' % album_cnt