# coding=utf-8

import codecs
import os
import datetime
import subprocess

# this must go first - this var is to be checked in defs.py
os.environ.setdefault('SERVER_PROFILE', 'DEVELOPMENT')

import defs
import utils
import sys

sys.stdout.write('Type title: ')
title = sys.stdin.readline().strip()
title = title.decode('cp866')

#title = u"Verasy / Верасы 1986 TEST"

assert type(title) == unicode
slug = utils.slugify(title)
print 'Title: %s' % title
print 'Slug: %s' % slug

if not len(slug):
    print 'No slug can be made for the title'
    sys.exit(1)

fname = os.path.join(defs.MARKDOWN_DIR, slug)
print 'Writing to %s' % fname
if os.path.exists(fname):
    print 'Article already exists: %s' % fname
    sys.exit(1)

f = codecs.open(fname, 'wb')
print >>f, '# title: %s' % title.encode('utf-8')
print >>f, '# date: %s' % datetime.datetime.now().strftime(defs.FORMAT_YMD_HMS)
print >>f, '# tags: '
f.close()

EDITOR = 'D:/portable/Sublime/sublime_text.exe'
subprocess.Popen([EDITOR, fname])