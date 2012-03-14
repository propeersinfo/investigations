import sys

import discogs_client as discogs

discogs.user_agent = 'PavelsClient/1.0 +http://sovietgroove.com'

artist = discogs.Artist('Hugo Montenegro')
print artist.data.keys()
for r in artist.releases:
	s = r.title
	year = r.data['year'] if r.data.has_key('year') else None
	if year:
		s = '%s (%s)' % (s, year)
	print s
	print >>sys.stderr, s
	#break