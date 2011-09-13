import re
import sys
import os

def only_dirs(root, short_file_names):
    return filter(lambda f: os.path.isdir(os.path.join(root,f)), short_file_names)

#def only_files(short_file_names):
#    return filter(lambda f: os.path.isfile(f), short_file_names)

def only_audio_files(root, short_file_names):
    def ok(short_file_name):
        long_file_name = os.path.join(root, short_file_name)
        return os.path.isfile(long_file_name) and re.search(r'.*\.(mp3|ogg|flac|ape)$', long_file_name, re.I)
    return sorted(filter(ok, short_file_names))

def cut_file_extension(input):
    m = re.search(r'^(.*)\.[\w\d]+$', input)
    return m.group(1) if m else input


def hms(seconds):
    seconds = int(seconds)
    hh = int(seconds / 3600)
    mm = int(seconds / 60) % 60
    ss = int(seconds) % 60
    if hh > 0:
        return "%d:%02d:%02d" % (hh, mm, ss)
    else:
        return "%d:%02d" % (mm, ss)


def ms(seconds):
    seconds = int(seconds)
    mm = int(seconds / 60)
    ss = int(seconds) % 60
    return "%d:%2d" % (mm, ss)


def single(list, def_value=None):
    return list[0] if len(list) > 0 else def_value


def fail(exit_code, msg):
    print >> sys.stderr, "error: %s" % msg
    sys.exit(exit_code)


def rewrite_file(fname, content):
    try:
        f = open(fname, 'w')
        print >> f, content
    finally:
        if f: f.close()
