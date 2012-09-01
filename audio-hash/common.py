# -*- coding: utf-8 -*-

import json
import sys
import re
import os
import zipfile
import glob
import codecs
import hashlib
import unicodedata
from StringIO import StringIO

MIN_FILES_IN_ALBUM = 2
RECOGNIZED_AUDIO_EXTENSIONS = [ 'mp3', 'flac', 'ape' ]


def check_hex_digest(hex_str):
    return not not re.match('[0-9A-Fa-f]{32}', hex_str)


def append_file(file, content):
    with codecs.open(file, 'a+', 'utf-8') as f:
        if content == '':
            f.write(content)
        else:
            print >>f, content


def write_file(file, content):
    with codecs.open(file, 'w', 'utf-8') as f:
        f.write(content)


# try to cut off the given start of the string
# case insensitive
def cut_start(title, pattern):
    if title.lower().find(pattern) == 0:
        title = title[len(pattern) : ]
    return title


#class CaseInsensitiveDict(dict):
#    def __setitem__(self, key, value):
#        return super(CaseInsensitiveDict, self).__setitem__(key.lower(), value)
#    def __getitem__(self, key):
#        return super(CaseInsensitiveDict, self).__getitem__(key.lower())
#    def get(self, key, default=None):
#        return super(CaseInsensitiveDict, self).get(key.lower(), default)
#    def __contains__(self):
#        raise Exception('is not implemented yet')
#    def has_key(self, key):
#        raise Exception('is not implemented yet')
#
#
#def collect_audio_hashes(audio_hash_file):
#    hash_by_file = CaseInsensitiveDict()
#    #hash_by_file = {}
#    with codecs.open(audio_hash_file, 'r', 'utf-8') as f:
#        for line in f:
#            hash, fname = line.strip().split(' ', 1)
#            hash = hash.strip()
#            fname = fname.strip()
#            if len(hash) > 0 and ord(hash[0]) == 65279:
#                # strip first three fucking unicode bytes written by mp3tag
#                hash = hash[1:]
#            if hash != '<ERROR>':
#                assert len(hash) == 32, u'Bad hash %s' % hash
#                hash_by_file[fname] = hash
#    return hash_by_file


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

def get_audio_files(dir, warnings=None):
    def warn(msg):
        if warnings:
            print >>warnings, msg

    deprecated_ext = [ 'ape' ]
    files_by_ext = {}
    for ext in RECOGNIZED_AUDIO_EXTENSIONS:
        mask = '*.%s' % ext
        files = [ file for file in glob.glob1(dir, mask) ]
        if len(files) > 0:
            files_by_ext[ext] = files

    if len(files_by_ext) == 0:
        return [], None
    elif len(files_by_ext) == 1:
        ext = files_by_ext.keys()[0]
        if ext.lower() in deprecated_ext:
            warn('format %s is deprecated' % ext)
            return [], None
        files = files_by_ext.values()[0]
        if len(files) >= MIN_FILES_IN_ALBUM:
            return sorted(files), ext
        else:
            warn('not enough files in directory to be an album: %s' % dir)
            return [], None
    else:
        warn('mixed audio codecs in %s' % dir)
        return [], None


# def get_album_format(dir):
# 	print 'dir is ', dir
# 	_, ext = get_audio_files(dir)
# 	return ext.upper()


class TrackContinuosityError(Exception):
    def __init__(self, msg):
        super(Exception, self).__init__(msg)


def check_files_continuosity(dir, files):
    ''' it is expected param 'files' is sorted already '''
    REGEX_01 = '^([0-9]{1,2})[ -_.].+'
    REGEX_A1 = '^([a-dA-D])([0-9]{1,2})[ -_.].+'
    if re.search(REGEX_01, files[0]):
        cnt = 1
        for file in files:
            m = re.search(REGEX_01, file)
            if m:
                pos = int(m.group(1))
                if pos != cnt:
                    raise TrackContinuosityError(u'files are not continuous in %s' % dir)
                cnt += 1
            else:
                raise TrackContinuosityError('files are not continuous in %s' % dir)
    elif re.search(REGEX_A1, files[0]):
        raise TrackContinuosityError(u'patterm A1 is not implemented yet for %s' % dir)
    else:
        raise TrackContinuosityError(u'unknown file pattern "%s" in %s' % (files[0][0:10], dir))


def calc_album_hash(hash_db, dir, afiles_short, warnings=None):
    def warn(msg):
        if warnings:
            print >>warnings, msg

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
            warn(u'audio hash not found for files[%d] in %s' % (i,dir))
            # print '- %s' % file_abs
            # for key in hash_db.keys():
            # 	print '-- %s' % key
            return None
        one_hash = one_hash.upper()
        #assert len(one_hash) == 32, 'Bad hash %s' % one_hash
        assert check_hex_digest(one_hash), 'Bad hash %s' % one_hash
        #assert int(one_hash,16) != 0, Exception(u'bad hash %s for file %s' % (one_hash, file_abs))
        if int(one_hash,16) == 0:
            # this may happen for wma, ogg or 24 bit flac encoded by foobar2000
            warn('zero audio hash in %s' % dir)
            return None
        #print one_hash, file
        ah.update(one_hash)
    return ah.hexdigest().upper()


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
        if len(self['tracks']) > 0:
            return os.path.splitext(self['tracks'][0]['file_name'])[1][1:].upper()
        else:
            return None


def scan_album_dir(dir, hash_db, warnings=sys.stderr):
    assert type(dir) == unicode
    #print u'Directory %s' % dir
    afiles_short, ext = get_audio_files(dir)
    if afiles_short:
        try:
            check_files_continuosity(dir, afiles_short)
            ah = calc_album_hash(hash_db, dir, afiles_short, warnings=warnings)
            if ah:
                dir_size, audio_size = get_album_sizes(dir)
                album = Album({
                    'album_hash': ah,
                    'path': dir,
                    'total_size': dir_size,
                    'audio_size': audio_size,
                })
                album['tracks'] = []
                for afile_short in afiles_short:
                    afile_full = os.path.join(dir, afile_short)
                    album['tracks'].append({
                        'file_name': afile_short,
                        'audio_hash': hash_db[afile_full],
                        'file_size': os.stat(afile_full).st_size,
                    })
                return album
        except TrackContinuosityError, e:
            if warnings:
                print >>warnings, u'%s' % e
    return None


def save_db_album(db_root, volume_name, album):
    json_file = os.path.join(db_root, volume_name, album['album_hash'])
    #json_text = json.dumps(album, indent=2)
    json_text = pretty_print_json_as_readable_unicode(album)

    with codecs.open(json_file, 'w', 'utf-8') as f:
        f.write(json_text)
    print 'file %s written' % json_file

    # make sure it could be parsed back
    json.loads(json_text)


class StreamTee:
    """Intercept a stream."""
    def __init__(self, target):
        self.target = target
    def write(self, s):
        s = self.intercept(s)
        self.target.write(s)
    def intercept(self, s):
        """Pass-through -- Overload this."""
        return s
    def flush(self):
        return self.target.flush()


class SafeStreamFilter(StreamTee):
    """Convert string traffic to to something safe."""
    def __init__(self, target):
        StreamTee.__init__(self, target)
        self.encoding = 'utf-8'
        self.errors = 'replace'
        self.encode_to = self.target.encoding
        print 'self.encode_to:', self.encode_to
        if not self.encode_to:
            #raise Exception('target.encoding is None (because of redirect)')
            self.encode_to = 'cp866'
    def intercept(self, s):
        return s.encode(self.encode_to, self.errors).decode(self.encode_to)
    @classmethod
    def substitute_stdout(cls):
        sys.stdout = SafeStreamFilter(sys.stdout)


# class counting_hash(dict):
#     def __init__(self):
#         super(counting_hash, self).__init__()
#     def increment(self, key):
#         if self.has_key(key):
#             assert isinstance(self[key], int)
#             self[key] = self[key] + 1
#         else:
#             self[key] = 1


class dict_of_lists(dict):
    def __init__(self):
        super(dict_of_lists, self).__init__()
    def append(self, key, value):
        if self.has_key(key):
            assert isinstance(self[key], list)
            self[key].append(value)
        else:
            self[key] = [ value ]


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


def format_size(num):
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%3.0f%s" % (num, x)
        num /= 1024.0


def format_size_mb(num):
    num = num / 1024.0 / 1024.0
    return "%3.0f" % (num)


# format an str/unicode json-string as one readable by humans
# because the standard json.sumps() produces all these '\xUUUU'
def pretty_print_json_as_readable_unicode(json_object):
    def do_level(out, root, level = 0):
        offset = '  ' * level
        offset2 = '  ' * (level+1)
        if isinstance(root, list):
            out.write('%s[\n' % (offset,))
            for i, item in enumerate(root):
                if i > 0: out.write('%s,\n' % offset)
                do_level(out, item, level+1)
            out.write('\n%s]' % (offset,))
        elif isinstance(root, dict):
            out.write('%s{\n' % (offset,))
            for i, key in enumerate(root.keys()):
                if i > 0: out.write('%s,\n' % '')
                out.write('%s"%s": ' % (offset2, key))
                do_level(out, root[key], level+1)
            out.write('\n%s}' % offset)
        elif isinstance(root, basestring):
            root = root.replace('\\', '\\\\').replace('"', '\\"').replace('\r', '\\r').replace('\n', '\\n')
            out.write('"%s"' % (root,))
        elif isinstance(root, (int, long, float)):
            out.write('%s%s' % (offset, root))
        else:
            raise Exception('unsupported yet type %s' % type(root))

    #assert isinstance(json_text, (basestring))
    out = StringIO()
    try:
        do_level(out, json_object)
        return out.getvalue()
    finally:
        out.close()

