import os
import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC

def get_single_audio_info(file):
    def flac(file_path):
        audio = FLAC(file_path)
        print "p p r i n t for %s" % file_path
        audio.pprint()
        print "p p r i n t"
        print audio
        return audio.info.length, audio.info.bitrate
    def mp3(file_path):
        audio = MP3(file_path)
        return audio.info.length, audio.info.bitrate
    handler = {
        'flac': flac,
        'mp3': mp3
    }.get(file.get_extension().lower())
    #print "ext", file.get_extension().lower()
    try :
        if handler:
            #print "handler: %s" % handler
            return handler(file.path)
        else:
            return (0, 0)
    except mutagen.mp3.error:
        print >>sys.stderr, "cannot parse file %s" % file.path
        return (0, 0)

"""
def get_audio_info(files):
	total_length = 0
	total_bitrate = 0
	total_bitrate_count = 0
	for file in files:
		#file = os.path.join(root, file)
		audio = MP3(file.path)
		total_length += audio.info.length
		total_bitrate += audio.info.bitrate
		total_bitrate_count += 1
	if total_bitrate_count > 0:
		return (total_length, total_bitrate / 1000 / total_bitrate_count)
	else:
		return (0, 0)
"""