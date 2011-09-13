import re
import sys

def cut_file_extension(input):
	m = re.search(r'^(.*)\.[\w\d]+$', input)
	return m.group(1) if m else input

def hms(seconds):
	seconds = int(seconds)
	hh = int(seconds / 3600)
	mm = int(seconds / 60) % 60
	ss = int(seconds) % 60
	return "%d:%2d:%2d" % (hh, mm, ss)

def ms(seconds):
	seconds = int(seconds)
	mm = int(seconds / 60)
	ss = int(seconds) % 60
	return "%d:%2d" % (mm, ss)

def single(list, def_value = None):
	return list[0] if len(list) > 0 else def_value

def fail(exit_code, msg):
	print >>sys.stderr, "error: %s" % msg
	sys.exit(exit_code)

def rewrite_file(fname, content):
	try:
		f = open(fname, 'w')
		print >>f, content
	finally:
		if f: f.close()
