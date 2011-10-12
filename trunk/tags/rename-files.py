# -*- coding: utf-8 -*-

import glob
import unicodedata
import re
import os
import sys

from mutagen.easyid3 import EasyID3

# TODO: make sure track numbers are continuous

def ascii_only(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')

def get_common_artist(audios):
    def to_string(obj):
        if obj is None or isinstance(obj, str) or isinstance(obj, unicode):
            return obj
        else:
            return obj['artist'][0]
    def funk(a,b):
        a = to_string(a)
        b = to_string(b)
        return a if a == b else None
    return reduce(funk, audios)


def check_tags(audio):
    for key in ['artist', 'title', 'album', 'tracknumber']:
        if not audio.has_key(key):
            raise Exception('there is no tag %s in an audio file' % key)
        assert len(audio[key]) == 1
        value = audio[key][0].strip()
        if value == None or value == '':
            raise Exception('there is no tag %s in an audio file' % key)

        trn = audio['tracknumber'][0]
        if re.match(r'\d{1,2}', trn):
            pass
        elif re.match(r'[ABCD]\d{1,2}', trn, re.I):
            pass
        else:
            raise Exception('tracknumber not valid: %s' % trn)

files = sorted(glob.glob(u'*.mp3'))
audios = [EasyID3(file) for file in files]
map(check_tags, audios)
common_artist = get_common_artist(audios)
print 'common_artist: %s' % common_artist

class ValueSet:
    def __init__(self):
        self.values = dict()
    def pass_value(self, value):
        self.values[value] = value
    def get_values(self):
        return self.values.keys()

def do_rename(actual_rename, force_no_artist=False):
    files_to_rename = 0
    for i in xrange(len(files)):
        file = files[i]
        audio = audios[i]
        tr_no = int(audio['tracknumber'][0])
        if force_no_artist:
            new_name = u'%02d. %s.mp3' % (tr_no, audio['title'][0])
        else:
            new_name = u'%02d. %s - %s.mp3' % (tr_no, audio['artist'][0], audio['title'][0])
        if file != new_name:
            files_to_rename += 1
        if actual_rename:
            os.rename(file, new_name)
        else:
            print u'>>%s' % ascii_only(file)
            print u'  %s' % ascii_only(new_name)
    if not actual_rename:
        return files_to_rename

force_no_artist = False or common_artist
files_to_rename = do_rename(False, force_no_artist=force_no_artist)
if files_to_rename > 0:
    sys.stdout.write('correct? [y/n] ')
    answer = sys.stdin.readline()
    if answer.lower().strip() == 'y':
        do_rename(True, force_no_artist=force_no_artist)
    else:
        print 'no rename'
else:
    print 'nothing to rename'