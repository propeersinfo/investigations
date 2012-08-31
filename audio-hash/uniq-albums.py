# -*- coding: utf-8 -*-

import sys
import json
import re
import os
import glob
import codecs
import hashlib

from common import SafeStreamFilter
from common import dict_of_lists
from common import get_album_sizes
from common import format_size_mb
from common import Album


DB_ROOT = '.\\DB'


def get_volumes():
	volumes = []
	all_album_hashes = dict_of_lists()
	for volume_name in os.listdir(DB_ROOT):
		volume_dir = os.path.join(DB_ROOT, volume_name)
		if not os.path.isdir(volume_dir):
			continue
		volume = {
			'name': volume_name,
		}
		for album_json_short in os.listdir(volume_dir):
			album_json_abs = os.path.join(volume_dir, album_json_short)
			try:
				with codecs.open(album_json_abs, 'r', 'utf-8') as f:
					album_obj = json.loads(f.read())
					ah = album_obj['album_hash']
					assert ah == album_json_short
					volume[ah] = album_obj
					all_album_hashes.append(ah, album_obj)
			except BaseException, e:
				print 'cannot read file %s' % album_json_abs
				raise e

		volumes.append(volume)

	hashes_unique     = [ (hash,albums[0]) for hash,albums in all_album_hashes.items() if len(albums) == 1 ]
	#hashes_duplicated = [ (hash,albums)    for hash,albums in all_album_hashes.items() if len(albums) >  1 ]

	return volumes, hashes_unique#, hashes_duplicated


if __name__ == '__main__':
	SafeStreamFilter.substitute_stdout()

	base_name = os.path.splitext(sys.argv[0])[0]
	list_file = '%s.list' % base_name
	#raise Exception(list_file)

	volumes, hashes_unique = get_volumes()

	# for volume in volumes:
	# 	print '- %s\t%s' % (volume['name'], len(volume.keys()))

	# print 'hashes_unique: %s' % len(hashes_unique)
	# print 'hashes_duplicated: %s' % len(hashes_duplicated)

	# sort by album['path']
	hashes_unique = sorted(hashes_unique, key = lambda tuple: tuple[1]['path'])

	with codecs.open(list_file, 'w', 'utf-8') as f:
		for (hash, album) in hashes_unique:
			album = Album(album)
			dir = album['path']
			dir_size = album['total_size']
			fmt = album.get_audio_format()
			line = u'%s %s %-4s %s' % (hash, format_size_mb(dir_size), fmt, dir)
			print >>f, line
			print >>sys.stdout, line
