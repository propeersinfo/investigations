# -*- coding: utf-8 -*-

import sys
import json
import re
import os
import glob
import codecs
import hashlib
import subprocess
from time import sleep

from common import archive_dir
from common import calc_album_hash
from common import get_audio_files
from common import collect_audio_hashes
from common import scan_album_dir
from common import save_db_album
from common import append_file
from common import SafeStreamFilter

ACTUAL_ZIP_AND_UPLOAD = True
DB_ROOT = '.\\DB'
NAROD_VOLUME = 'narod'
ARCHIVE_TEMP_DIR = 'd:\\temp'
HASH_DB_FILE = 'audio_hash_edge.txt'
SLEEP_SEC = 5
FAILURE_LIST = 'upload-narod.failure'
SUCCESS_LIST = 'upload-narod.success'


def do_upload(zip_file):
	cmd = [ 'up-arkiv.bat', zip_file ]
	
	print 'running process: %s' % cmd
	sys.stdout.flush()

	if ACTUAL_ZIP_AND_UPLOAD:
		#p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		p = subprocess.Popen(cmd, stdin=None, stdout=subprocess.PIPE, stderr=None)
		stdout = p.stdout.read()
		#stderr = p.stderr.read()
	else:
		stdout = 'http://narod.ru/xxx'
		#stderr = 'errrrr'

	print 'logging stdout:'
	print stdout

	#print 'logging stderr:'
	#print '-disabled-' # stderr

	stdout = stdout.strip()
	if stdout.lower().find('http://') == 0:
		print 'file uploaded OK'
		return stdout
	else:
		print 'WARNING! file NOT uploaded'
		return None


def handle_dir(dir, hash1, hash_db, last_iteration):
	audio_files, _ = get_audio_files(dir)
	hash2 = calc_album_hash(hash_db, dir, audio_files, warnings=sys.stdout)
	assert hash1 == hash2, '%s vs %s' % (hash1, hash2)
	
	db_album_file = os.path.join(DB_ROOT, NAROD_VOLUME, hash1)
	if os.path.exists(db_album_file):
		#append_file(FAILURE_LIST, '%s %s' % (hash1, dir))
		print ''
		print 'WARINIG! db_album_file already exists: %s' % db_album_file
		print 'No zip, no upload'
		print ''
	else:
		archive_file = os.path.join(ARCHIVE_TEMP_DIR, '%s.zip' % hash1)
		print 'zipping into %s...' % archive_file
		if ACTUAL_ZIP_AND_UPLOAD:
			archive_dir(dir, archive_file)

		sys.stdout.flush()

		narod_url = do_upload(archive_file)
		if narod_url:
			if ACTUAL_ZIP_AND_UPLOAD:
				album_obj = scan_album_dir(dir, hash_db)
				album_obj['url'] = narod_url
				album_obj['total_size'] = os.stat(archive_file).st_size
				#print 'WARNING! db file not written!'
				save_db_album(DB_ROOT, NAROD_VOLUME, album_obj)
			append_file(SUCCESS_LIST, '%s %s' % (hash1, dir))

			if not last_iteration and ACTUAL_ZIP_AND_UPLOAD:
				print 'sleeping for %s seconds' % SLEEP_SEC
				sleep(SLEEP_SEC)

		else:
			append_file(FAILURE_LIST, '%s %s' % (hash1, dir))

		if os.path.exists(archive_file):
			os.remove(archive_file)


def main():
	SafeStreamFilter.substitute_stdout()

	bulk_file = 'upload.queue'
	assert os.path.exists(bulk_file)

	hash_db = collect_audio_hashes(HASH_DB_FILE)

	volume_dir = os.path.join(DB_ROOT, NAROD_VOLUME)
	if not os.path.exists(volume_dir):
		os.mkdir(volume_dir)

	if os.path.exists(SUCCESS_LIST): os.remove(SUCCESS_LIST)
	if os.path.exists(FAILURE_LIST): os.remove(FAILURE_LIST)

	append_file(SUCCESS_LIST, '')
	append_file(FAILURE_LIST, '')

	entries = []
	with codecs.open(bulk_file, 'r', 'utf-8') as f:
		for line in f:
			hash1, size, fmt, dir = re.split(r'\s+', line.strip(), 3)
			if dir:
				if not os.path.exists(dir):
					raise Exception('directory does not exist: %s' % dir)
				entries.append((hash1, size, fmt, dir))

	for i,tuple in enumerate(entries):
		hash1, size, fmt, dir = tuple
		print '--------------- Album %d/%d ----------------' % (i+1, len(entries))
		print '%s (%s MB)' % (dir, size)

		last_iteration = i+1 == len(entries)
		handle_dir(dir, hash1, hash_db, last_iteration)

		sys.stdout.flush()

	print 'FINISHED'
	print 'Press Enter'
	sys.stdout.flush()
	sys.stdin.readline()


if __name__ == '__main__':	
	main()
