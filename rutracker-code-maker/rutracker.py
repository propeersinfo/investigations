import re
import glob
import os
import sys
import subprocess
import tempfile

from fs import Dir
from utils import *
import media_info


def get_root_image():
    root_image = single(glob.glob("*.jpg"))
    assert root_image, "cannot find an image of artist"
    return root_image


def command_upload_images():
    print "command_upload..."
    db = tempfile.mktemp()


def command_generate_bbcode():
    print "command_generate_bbcode..."

    root = Dir('.').collect_sub_files()
    print 'Size: %s bytes' % root.get_size()
    #print 'Length: %s' % hms(root.get_audio_length())
    audio_info = root.collect_audio_info()
    print 'total length: %s' % hms(audio_info.get_length())
    print 'average bitrate: %s kbps' % audio_info.get_average_bitrate()

    def on_dir(dir, deepness):
        str_offset = "  " * (deepness + 1)
        aa = get_local_audio_files(dir)
        for img in dir.get_associated_images():
            print "%s[img=right]%s[/img]" % (str_offset, img.get_thumbnail_image_url())
        for a in aa:
            str_name = cut_file_extension(a.get_last_name())
            length = a.get_audio_length()
            str_length = " [color=grey]%s[/color]" % hms(length) if length else ""
            print "%s%s%s" % (str_offset, str_name, str_length)

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