# -*- coding: utf-8 -*-

from pprint import pprint
import sys
import os
import glob
import re
import math
import unicodedata

import mutagen
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

import discogs_client as discogs

discogs.user_agent = 'PavelsClient/1.0 +http://sovietgroove.com'
release = discogs.Release(int(sys.argv[1]))
#pprint(release)

#print [a.name for a in release.artists[0]]
#print release.title
#print release.master

"""
track - a hash:
+ title: string
+ artists: list of <Artist>'s
+ duration: 2:08
+ position: A1
"""

def get_discogs_track_artist_string(track):
	aa = []
	for a in track['artists']:
		if type(a) == unicode:
			pass
		else:
			aa.append(a.name)
	if len(aa) > 0:
		return ', '.join(aa)
	else:
		return 'Unknown Artist'

def get_discogs_track_length(track):
	if track.has_key('duration'):
		m = re.match(r'(\d+):(\d+)', track['duration'])
		if m:
			min = int(m.group(1))
			sec = int(m.group(2))
			return min * 60 + sec
		else:
			raise Exception('cannot parse duration: %s' % track['duration'])
	else:
		return None

def get_duration_difference(dur1, dur2):
	dur1 = float(dur1)
	dur2 = float(dur2)
	diff = (dur1 - dur2) / min(dur1, dur2)
	return math.fabs(diff)

def ascii_only(s):
	return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').lower()

def compare_discogs_vs_files(release, discogs_tracks, hdd_files):
	DUR_DIFF_GATE = 0.10
	if len(discogs_tracks) != len(hdd_files):
		raise Exception('Amount of tracks differs: %d vs %d' % (len(discogs_tracks), len(hdd_files)))
	for i in xrange(len(hdd_files)):
		track = discogs_tracks[i]
		track_len = get_discogs_track_length(track)
		#print 'track artist: %s' % ascii_only(get_discogs_track_artist_string(track))
		#print 'track title: %s' % ascii_only(track['title'])
		#print 'track dur: %s' % track_len
		file = hdd_files[i]
		mp3 = MP3(file)
		#print 'mp3 dur: %s' % mp3.info.length
		diff = get_duration_difference(track_len, mp3.info.length)
		#print 'dur difference: %s' % diff
		if diff > DUR_DIFF_GATE:
			raise Exception('tracks durations differs too much: %s vs %s' \
				% (mp3.info.length, track_len))
	for i in xrange(len(hdd_files)):
		track = discogs_tracks[i]
		mp3 = EasyID3(hdd_files[i])
		mp3['artist'] = get_discogs_track_artist_string(track)
		mp3['album'] = release.title
		mp3['title'] = track['title']
		mp3['tracknumber'] = track['position']
		mp3['date'] = str(release.data['year']) if release.data.has_key('year') else ''
		mp3.save()

compare_discogs_vs_files(release, release.tracklist, sorted(glob.glob("*.mp3")))