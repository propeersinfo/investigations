import os
import mutagen
from mutagen.mp3 import MP3

def get_single_audio_info(file):
    try:
        audio = MP3(file.path)
        return audio.info.length, audio.info.bitrate
    #except mutagen.mp3.HeaderNotFoundError:
    except RuntimeError:
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