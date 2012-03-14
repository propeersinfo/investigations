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
from mutagen.apev2 import APEv2
from mutagen.easyid3 import EasyID3

import discogs_client as discogs

import win32clipboard

def get_clipboard_text():
    try:
        win32clipboard.OpenClipboard()
        return win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
    finally:
        win32clipboard.CloseClipboard()

def read_file(file):
    f = None
    try:
        f = open(file, 'r')
        return f.read()
    finally:
        if f: f.close()

def rewrite_file(file, content):
    content = str(content)
    f = None
    try:
        f = open(file, 'w')
        f.write(content)
    finally:
        if f: f.close()

def load_easy_id3_tags(file):
	try:
		return EasyID3(file)
	except mutagen.id3.ID3NoHeaderError:
		return EasyID3()

def load_ape_tags(file):
	try:
		return APEv2(file)
	except mutagen.apev2.APENoHeaderError:
		return APEv2()

def load_flac_tags(file):
	try:
		return FLAC(file)
	except mutagen.flac.FLACNoHeaderError:
		return FLAC()

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
    # for t in discogs_tracks:
    #     print t
    #     sys.exit(111)

    DUR_DIFF_GATE = 0.20
    if len(discogs_tracks) != len(hdd_files):
        raise Exception('Amount of tracks differs: %d vs %d' % (len(discogs_tracks), len(hdd_files)))
    # make sure track lengths differs not so much
    # for i in xrange(len(hdd_files)):
    #     track = discogs_tracks[i]
    #     track_len = get_discogs_track_length(track)
    #     file = hdd_files[i]
    #     mp3 = MP3(file)
    #     if track_len:
    #         diff = get_duration_difference(track_len, mp3.info.length)
    #         if diff > DUR_DIFF_GATE:
    #             raise Exception('tracks durations differs too much: %s vs %s' % (mp3.info.length, track_len))

    def do_pass(really_do):
        for i in xrange(len(hdd_files)):
            track = discogs_tracks[i]
            hdd_file = hdd_files[i]
            artist = get_discogs_track_artist_string(track, release)
            title = track['title']
            _, ext = os.path.splitext(hdd_file)
            ext = ext.lower()
            #print 'ext: %s' % ext
            mp3s = []
            if ext == '.mp3':
                mp3s.append(load_easy_id3_tags(hdd_file))
                mp3s.append(load_ape_tags(hdd_file))
            elif ext == '.flac':
                mp3s.append(load_flac_tags(hdd_file))
            else:
                raise Exception('inacceptable file extension for file %s' % hdd_file)
            assert len(mp3s) > 0

            for mp3 in mp3s:
                mp3['artist'] = artist
                mp3['album'] = release.title
                mp3['title'] = title
                mp3['tracknumber'] = track['position']
                year_str = str(release.data['year']) if release.data.has_key('year') else ''
                if type(mp3) == EasyID3:
                    mp3['date'] = year_str
                else:
                    mp3['track'] = track['position']
                    mp3['year'] = year_str

            if really_do:
                for mp3 in mp3s:
                    mp3.save(hdd_file)
            else:
                print '%s' % ascii_only(hdd_files[i])
                title = ascii_only(title)
                artist = ascii_only(artist)
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
    if m:
        return int(m.group(1))
    else:
        return None

#print parse_discogs_id(get_clipboard_text())
#sys.exit(111)

discogs.user_agent = 'PavelClient/1.0 +http://sovietgroove.com'
if len(sys.argv) == 1:
    release_id = parse_discogs_id(get_clipboard_text())
    if release_id:
        print 'taking release_id from clipboard: %d' % release_id
    else:
        release_id = None
        #release_id = read_file('discogs-id')
        #print 'taking release_id from file'
else:
    release_id = parse_discogs_id(sys.argv[1])
if not release_id:
    raise Exception('no correct release_id specified')
release_id = int(release_id)
#print 'release_id: %d' % release_id
release = discogs.Release(release_id)
audios = glob.glob(u"*.mp3")
if not len(audios):
    audios = glob.glob(u"*.flac")
audios = sorted(audios, key=unicode.lower)
tracks = release.tracklist
tracks = filter(lambda t: t['type'].lower() != 'index track', tracks)
compare_discogs_vs_files(release, tracks, audios)
rewrite_file('discogs-id', release_id)