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
from mutagen.flac import FLAC
from mutagen.easyid3 import EasyID3

import discogs_client as discogs

def get_discogs_track_artist_string(track, release):
	#print 'release: %s' % release.artists
	src = []
	if len(src) == 0:
		src = track['artists']
	if len(src) == 0:
		src = release.artists
	if len(src) == 0:
		src = []
	dst = []
	for a in src:
		if type(a) == unicode:
			pass
		else:
			dst.append(a.name)
	if len(dst) > 0:
		return ', '.join(dst)
	else:
		return 'Unknown Artist'

def get_discogs_track_length(track):
    if not track.has_key('duration'):
        return None

    value = track['duration']

    if value == '':
        return None

	m = re.match(r'(\d+):(\d+)', value)
	if m:
		min = int(m.group(1))
		sec = int(m.group(2))
		return min * 60 + sec
	else:
		raise Exception('cannot parse duration: %s' % value)

def get_duration_difference(dur1, dur2):
	dur1 = float(dur1)
	dur2 = float(dur2)
	diff = (dur1 - dur2) / min(dur1, dur2)
	return math.fabs(diff)

def ascii_only(s):
	return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')


def compare_discogs_vs_files(release, discogs_tracks, hdd_files):
    DUR_DIFF_GATE = 0.50
    if len(discogs_tracks) != len(hdd_files):
        raise Exception('Amount of tracks differs: %d vs %d' % (len(discogs_tracks), len(hdd_files)))
    # make sure track lengths differs not so much
    for i in xrange(len(hdd_files)):
        track = discogs_tracks[i]
        track_len = get_discogs_track_length(track)
        file = hdd_files[i]
        mp3 = MP3(file)
        if track_len:
            diff = get_duration_difference(track_len, mp3.info.length)
            if diff > DUR_DIFF_GATE:
                raise Exception('tracks durations differs too much: %s vs %s' % (mp3.info.length, track_len))

    def do_pass(really_do):
        for i in xrange(len(hdd_files)):
            track = discogs_tracks[i]
            hdd_file = hdd_files[i]
            artist = get_discogs_track_artist_string(track, release)
            title = track['title']
            _, ext = os.path.splitext(hdd_file)
            ext = ext.lower()
            #print 'ext: %s' % ext
            if ext == '.mp3':
                mp3 = EasyID3(hdd_file)
            elif ext == '.flac':
                mp3 = FLAC(hdd_file)
            else:
                raise Exception('inacceptable file extension for file %s' % hdd_file)

            mp3['artist'] = artist
            mp3['album'] = release.title
            mp3['title'] = title
            mp3['tracknumber'] = track['position']
            mp3['date'] = str(release.data['year']) if release.data.has_key('year') else ''

            if really_do:
                mp3.save()
            else:
                print '%s' % hdd_files[i]
                print '%s. %s / %s' % (track['position'], title, artist)
                print ''
    do_pass(False)
    #raise Exception('exiting')
    sys.stdout.write('correct? [y/N] ')
    answer = sys.stdin.readline()
    if answer.lower().strip() == 'y':
        do_pass(True)
    else:
        print "no action"

def parse_discogs_id(s):
    regex = re.compile('http://www.discogs.com/.*release/(\d+)', re.I)
    m = re.search(regex, s)
    assert m
    return int(m.group(1))

discogs.user_agent = 'PavelsClient/1.0 +http://sovietgroove.com'
release_id = parse_discogs_id(sys.argv[1])
#print 'release_id: %d' % release_id
release = discogs.Release(release_id)
audios = glob.glob("*.mp3")
if not len(audios):
    audios = glob.glob("*.flac")
audios = sorted(audios)
compare_discogs_vs_files(release, release.tracklist, audios)