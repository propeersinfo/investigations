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


class DirInfo():
    def __init__(self, path, dirs, files):
        self.path = path
        self.length = 0
        self.bitrate = None
        self.media_files = files


def get_dir_info(root, dirs, files):
    leave_media_files = lambda fname: re.search(r'.*\.(mp3|ogg|flac|ape)$', fname, re.I)
    media_files = filter(leave_media_files, files)
    info = DirInfo(root, dirs, media_files)
    #print 'root:', root
    #print 'files:', files
    (length, bitrate) = media_info.get_dir_media_info(root, media_files)
    if length:
        info.length = length
        info.bitrate = int(bitrate / 1000)
    return info


def command_upload_images():
    print "command_upload..."

#upload_image(get_root_image())

def command_generate_bbcode():
    print "command_generate_bbcode..."
    total_length = 0
    for root, dirs, files in os.walk('.'):
        info = get_dir_info(root, dirs, files)
        if info:
            total_length += info.length
            print "[spoiler=\"%s (%s kbps)\"]" % (info.path, info.bitrate)
            print "[img=right]%s[/img]" % (None)
            for file in info.media_files:
                print "%s" % (cut_file_extension(file))
            print '[/spoiler]'
            print ''
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