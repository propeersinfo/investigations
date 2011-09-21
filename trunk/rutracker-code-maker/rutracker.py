import re
import glob
import os
import sys
import subprocess
from fs import Dir

from utils import *
import media_info

# objective related functions

#def upload_image(image_file):
#    image_file = os.path.abspath(image_file)
#    link_file = '%s.imagelink' % image_file
#    cwd = os.getcwd()
#    uploader_dir = "C:\\Portable\\zenden-image-uploader"
#    upload_cmd = ['imgupload.exe', '--server', 'fastpic.ru', '--codelang', 'bbcode', '--codetype', 'Images', image_file]
#    try:
#        print "uploading image '%s'" % image_file
#        os.chdir(uploader_dir)
#        #p = subprocess.Popen(upload_cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#        #(bbcode, err) = p.communicate()
#        #print "out: %s" % out
#        #print 'err: %s' % err
#        bbcode = "http://faspic.ru/qwertyuiop"
#        rewrite_file(link_file, bbcode)
#    finally:
#        os.chdir(cwd)


def get_root_image():
    root_image = single(glob.glob("*.jpg"))
    assert root_image, "cannot find an image of artist"
    return root_image


def command_upload_images():
    print "command_upload..."



def command_generate_bbcode():
    print "command_generate_bbcode..."

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
            print '%s[spoiler="%s / %s kbps"]' % (offset, title, btr)
            for dir in root_dir.dirs:
                walk_deep_down(dir, dir_handler, deepness+1)
            dir_handler(root_dir, deepness)
            print '%s[/spoiler]' % offset
    walk_deep_down(root, on_dir)

def command_make_torrent():
    pass

if __name__ == '__main__':
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