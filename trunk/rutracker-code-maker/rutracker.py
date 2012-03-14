import re
import glob
import os
import sys
import subprocess
import tempfile
import StringIO
import codecs

from fs import Dir
from utils import *
import media_info
import clipboard

class StringBuffer():
    def __init__(self):
        self.list = []
    def add(self, str):
        self.list.append(str)
    def getvalue(self):
        return '\r\n'.join(self.list)

def get_root_image():
    root_image = single(glob.glob("*.jpg"))
    assert root_image, "cannot find an image of artist"
    return root_image


def command_generate_bbcode():
    print >>sys.stderr, "command_generate_bbcode..."
    output = StringBuffer()

    def print_dir(dir, deepness):
        str_offset = "  " * (deepness + 1)
        aa = get_local_audio_files(dir)
        total_length = 0
        for a in aa:
            str_name = cut_file_extension(a.get_last_name())
            length = a.get_audio_length()
            total_length += length
            str_length = " [color=grey]%s[/color]" % hms(length) if length else ""
            output.add("%s%s%s" % (str_offset, str_name, str_length))
        output.add("%s[color=grey]Total: %s[/color]" % (str_offset, hms(total_length)))

    def walk_deep_down(root_dir, dir_handler, deepness=0):
        if root_dir.contains_audio_recursively():
            str_offset = u"  " * deepness
            str_offset_2 = u"  " * (deepness+1)
            str_title = root_dir.get_last_name()
            audio_info = root_dir.collect_audio_info()
            len = hms(audio_info.get_length())
            str_btr = u"%s kbps" % audio_info.get_average_bitrate()
            #len = hms(root_dir.get_audio_length())
            #btr = root.get_bitrate_value()
            #print 'type(str_title) = %s' % type(str_title)
            #x = u'%s' % (str_offset)
            #x = u'%s' % unicode(str_title)
            #x = u'%s%s' % (str_offset, str_title)
            #output.add(x)
            output.add('%s[spoiler="%s / %s"]' % (unicode(str_offset), unicode(str_title), unicode(str_btr)))
            for img in root_dir.get_associated_images():
                output.add("%s[url=%s][img=right]%s[/img][/url]" % \
                    (str_offset_2, img.get_full_page_url(), img.get_thumbnail_image_url()))
            for dir in root_dir.dirs:
                walk_deep_down(dir, dir_handler, deepness+1)
            dir_handler(root_dir, deepness)
            output.add('%s[/spoiler]' % str_offset)

    root = Dir(u'.').collect_sub_files()
    audio_info = root.collect_audio_info()
    size_bytes = root.get_size()
    output.add('Size: %s bytes' % size_bytes)
    output.add('Total length: %s' % hms(audio_info.get_length()))
    output.add('Average bitrate: %s kbps' % audio_info.get_average_bitrate())
    print_chunk_sizes(output, size_bytes)
    walk_deep_down(root, print_dir)

    report = output.getvalue()
    #print report
    out = codecs.open("rutracker.txt", "w", "utf-8")
    out.write(report)
    out.close()
    #clipboard.copy_text(report)
    #output.close()

def print_chunk_sizes(output, total_size):
    chunk_num = total_size / (256 * 1024)
    for chunk_size in [ '256KB', '512KB', '1MB', '2MB', '4MB' ]:
        output.add("Chunk size %+5s -> %4d chunks" % (chunk_size, chunk_num))
        chunk_num /= 2

def command_make_torrent():
    pass

if __name__ == '__main__':
    #print "encoding: %s" % getattr(sys.stdout, 'encoding', None)
    #print "encoding: %s" % getattr(sys.stderr, 'encoding', None)
    commands = {
        'code': command_generate_bbcode,
        'mktorrent': command_make_torrent
    }
    if len(sys.argv) != 2:
        fail(1, "specify a command: %s" % commands.keys())
    command_name = sys.argv[1]
    if not commands.has_key(command_name):
        fail(1, "there is no command %s" % command_name)
    commands[command_name]()