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
        def __str__(self):
            return "Dir(%s)" % self.path
        def get_last_name(self):
            return os.path.split(self.path)[1]
        def contains_audio_recursively(self):
            for f in self.reg_files:
                if is_supported_audio_file(f.path):
                    return True
            for dir in self.dirs:
                if dir.contains_audio_recursively():
                    return True
            return False
        def collect_audio_info(self, collector = None):
            class Collector():
                def __init__(self):
                    self.bitrate_sum = 0
                    self.bitrate_cnt = 0
                    self.length = 0
                def collect(self, track):
                    len, brt = media_info.get_single_audio_info(track)
                    if len and brt:
                        self.bitrate_cnt += 1
                        self.bitrate_sum += brt
                        self.length += len
                def get_length(self):
                    return self.length
                def get_average_bitrate(self):
                    return (self.bitrate_sum / 1000 / self.bitrate_cnt) if (self.bitrate_cnt > 0) else 0
            if collector is None:
                collector = Collector()
            for track in self.reg_files:
                collector.collect(track)
            for dir in self.dirs:
                dir.collect_audio_info(collector)
            return collector

    root = Dir('.').collect_sub_files()
    print 'Size: %s bytes' % root.get_size()
    #print 'Length: %s' % hms(root.get_audio_length())
    audio_info = root.collect_audio_info()
    print 'total length: %s' % hms(audio_info.get_length())
    print 'average bitrate: %s' % audio_info.get_average_bitrate()

    def on_dir(dir, deepness):
        offset = "  " * (deepness + 1)
        mm = get_local_audio_files(dir)
        if len(mm) > 0:
            for m in mm:
                print "%s%s" % (offset, cut_file_extension(m.get_last_name()))

    def walk_deep_down(root_dir, dir_handler, deepness=0):
        if root_dir.contains_audio_recursively():
            offset = "  " * deepness
            title = root_dir.get_last_name()
            audio_info = root_dir.collect_audio_info()
            len = hms(audio_info.get_length())
            btr = audio_info.get_average_bitrate()
            #len = hms(root_dir.get_audio_length())
            #btr = root.get_bitrate_value()
            print '%s[spoiler="%s / %s kbps / %s"]' % (offset, title, btr, len)
            for dir in root_dir.dirs:
                walk_deep_down(dir, dir_handler, deepness+1)
            dir_handler(root_dir, deepness)
            print '%s[/spoiler]' % offset
    walk_deep_down(root, on_dir)

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