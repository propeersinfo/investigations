import re
from BeautifulSoup import BeautifulSoup, NavigableString
from soupselect import select
import sys
import datetime
import codecs
import HTMLParser
import glob

def read_file(path, charset = "utf-8"):
  f = codecs.open(path, "r", charset)
  try:
    return f.read()
  finally:
    f.close()

for index_file in sorted(glob.glob('index.htm*')):
	#print index_file
	soup = BeautifulSoup(read_file(index_file))
	for a in select(soup, "div.month ul li a"):
		print '%s%s' % ('http://my.opera.com', a['href'])