import re
import glob
import os
import sys
import subprocess

from utils import *
import media_info

# objective related functions

def upload_image(image_file):
    image_file = os.path.abspath(image_file)
    link_file = '%s.imagelink' % image_file
    cwd = os.getcwd()
    uploader_dir = "C:\\Portable\\zenden-image-uploader"
    upload_cmd = ['imgupload.exe', '--server', 'fastpic.ru', '--codelang', 'bbcode', '--codetype', 'Images', image_file]
    try:
        print "uploading image '%s'" % image_file
        os.chdir(uploader_dir)
        #p = subprocess.Popen(upload_cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #(bbcode, err) = p.communicate()
        #print "out: %s" % out
        #print 'err: %s' % err
        bbcode = "http://faspic.ru/qwertyuiop"
        rewrite_file(link_file, bbcode)
    finally:
        os.chdir(cwd)


def get_root_image():
    root_image = single(glob.glob("*.jpg"))
    assert root_image, "cannot find an image of artist"
    return root_image


def command_upload_images():
    print "command_upload..."

class UniqueOutputPiece(object):
    def __init__(self, text):
        self.text = text
        self.printed = False
    def print_itself(self):
        if self.printed:
            #print "SKIPPING"
            pass
        #elif re.search(r'.*album.*', self.text, re.IGNORECASE):
        else:
            print self.text#, self.__hash__()
            self.printed = True

def short_names_to_long(base, short_names):
    return map(lambda n: os.path.join(base, n), short_names)

def command_generate_bbcode():
    print "command_generate_bbcode..."

    class RegFile():
        def __init__(self, path):
            self.path = path
        def get_size(self):
            return os.path.getsize(self.path)
        def __str__(self):
            return "File(%s)" % self.path
        def get_last_name(self):
            return os.path.split(self.path)[1]

    class Dir():
        def __init__(self, path):
            self.path = path
            self.dirs = []
            self.reg_files = []
        def collect_sub_files(self):
            for file in short_names_to_long(self.path, os.listdir(self.path)):
                if os.path.isdir(file):
                    sub_dir = Dir(file)
                    self.dirs.append(sub_dir)
                    sub_dir.collect_sub_files()
                else:
                    reg_file = RegFile(file)
                    self.reg_files.append(reg_file)
            return self
        def get_size(self):
            size = 0
            for f in self.reg_files: size += f.get_size()
            for f in self.dirs: size += f.get_size()
            return size
#        def walk_deep_down(self, dir_handler, deepness=0):
#            dir_handler(self, deepness)
#            for dir in self.dirs:
#                dir.walk_deep_down(dir_handler, deepness+1)
        def __str__(self):
            return "Dir(%s)" % self.path
        def get_last_name(self):
            return os.path.split(self.path)[1]

    root = Dir('.').collect_sub_files()
    print 'root: %s' % root
    print 'root: %s bytes' % root.get_size()

    def get_local_audio_files(dir):
        return filter(lambda f: is_supported_audio_file(f.path), dir.reg_files)

    def on_dir(dir, deepness):
        offset = "  " * (deepness + 1)
        mm = get_local_audio_files(dir)
        if len(mm) > 0:
            for m in mm:
                print "%s%s" % (offset, cut_file_extension(m.get_last_name()))
    #root.walk_deep_down(on_dir)
    def walk_deep_down(root_dir, dir_handler, deepness=0):
        offset = "  " * deepness
        print '%s[spoiler="%s"]' % (offset, root_dir.get_last_name())
        for dir in root_dir.dirs:
            walk_deep_down(dir, dir_handler, deepness+1)
        dir_handler(root_dir, deepness)
        print '%s[/spoiler]' % offset
    walk_deep_down(root, on_dir)

"""
def command_generate_bbcode():
    print "command_generate_bbcode..."

    total_length = 0

    def one_dir(root_long, root_short, offset, print_text_before_old = None):
        sub_files = os.listdir(root_long)
        sub_dirs = only_dirs(root_long, sub_files)
        audio_files = only_audio_files(root_long, sub_files)
        (dir_length, dir_bitrate) = media_info.get_dir_media_info(root_long, audio_files)
        #total_length += dir_length

        s_offset = " " * offset * 2
        s_offset_2 = " " * (offset+1) * 2
        s_bitrate = " (%s kbps)" % dir_bitrate if dir_bitrate else ""

        text_before = UniqueOutputPiece('%s[spoiler="%s%s"]' % (s_offset, root_short, s_bitrate))
        def print_text_before_new():
            if print_text_before_old:
                print_text_before_old()
            text_before.print_itself()

        if len(audio_files) > 0:
            print_text_before_new()
        for dir in sub_dirs:
            one_dir(os.path.join(root_long, dir), dir, offset+1, print_text_before_new)
        for audio in audio_files:
            print "%s%s" % (s_offset_2, cut_file_extension(audio))
        if text_before.printed:
            print '%s[/spoiler]' % (s_offset)

    root = "."
    one_dir(root, root, 0)
    print "total length: %s" % hms(total_length)
"""

def command_make_torrent():
    pass

# main

commands = {
    'upload-images': command_upload_images,
    'code': command_generate_bbcode,
    'mktorrent': command_make_torrent
}
if len(sys.argv) != 2:
    fail(1, "specify a command: %s" % commands.keys())
command_name = sys.argv[1]
if not commands.has_key(command_name):
    fail(1, "there is no command %s" % command_name)
commands[command_name]()