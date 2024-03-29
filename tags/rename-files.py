# -*- coding: utf-8 -*-

import glob
import unicodedata
import re
import os
import sys

from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC

# TODO: make sure track numbers are continuous

def filter_tag_text(s):
    #print 's: %s' % s
    regexps = {
        # characters inacceptable for certain FS's
        r'[/\\]': '#',
        r'([^\s]):([^\s])': '\\1-\\2',  # aaa:bbb  => aaa-bbb
        r':': ' - ',                    # aaa: bbb => aaa - bbb
        r';': '.',
        #r';': ' # ',
        r'[\?\*<>]': '',
        r'["]': '\'',
        # to be applied last
        r'\.+$': '',   # any trailing dots
        r'\s+': ' ', # two spaces to one
    }
    for regex in regexps:
        replace = regexps[regex]
        #print '%s --> <%s>' % (regex, replace)
        s = re.sub(regex, replace, s)
    s = s.strip()
    return s

def ascii_only(s):
    #return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')
    return unicode(s)

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
if not len(files):
    files = sorted(glob.glob(u'*.flac'))
    audios = [ FLAC(file) for file in files ]
else:
    audios = [ EasyID3(file) for file in files ]
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
    def get_track_number_string(tr_no):
        try:
            tr_no_str = '%02d' % int(tr_no)
        except ValueError:
            tr_no_str = str(tr_no)
            m = re.match('[a-dA-D]\d\d?', tr_no_str)
            if m:
                pass
            else:
                m = re.match('(\d\d?)/\d\d?', tr_no_str)
                if m:
                    tr_no_str = '%02d' % int(m.group(1))
                else:
                    raise Exception('cannot parse track no: %s' % tr_no)
        assert tr_no_str
        return tr_no_str

    files_to_rename = 0
    for i in xrange(len(files)):
        file = files[i]
        audio = audios[i]
        tr_no_str = get_track_number_string(audio['tracknumber'][0])
        title = filter_tag_text(audio['title'][0])
        artist = filter_tag_text(audio['artist'][0])
        _, ext = os.path.splitext(file)
        if force_no_artist:
            new_name = u'%s. %s%s' % (tr_no_str, title, ext)
        else:
            new_name = u'%s. %s - %s%s' % (tr_no_str, artist, title, ext)
        if file != new_name:
            files_to_rename += 1
        if actual_rename:
            os.rename(file, new_name)
        else:
            print u'>>%s' % ascii_only(file)
            print u'  %s' % ascii_only(new_name)
    if not actual_rename:
        return files_to_rename

force_no_artist = True if (len(sys.argv) == 2 and sys.argv[1] == 't') else False
force_no_artist = force_no_artist or common_artist
files_to_rename = do_rename(False, force_no_artist=force_no_artist)
if files_to_rename > 0:
    sys.stdout.write('correct? [y/N] ')
    answer = sys.stdin.readline()
    if answer.lower().strip() == 'y':
        do_rename(True, force_no_artist=force_no_artist)
    else:
        print 'no rename'
else:
    print 'nothing to rename'