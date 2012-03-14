import sys
import glob

audios = glob.glob(u'*.mp3')
if len(audios) == 0:
	audios = glob.glob(u'*.flac')
assert len(audios) > 0
audios = sorted(audios)
