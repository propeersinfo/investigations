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