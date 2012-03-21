import random
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

#class EtagExperiment(webapp.RequestHandler):
#    def get(self):
#        html = 'Response code 304 gonna be set if header If-None-Matched provided<br>%s' % random.random()
#        etag_actual = '1234567890'
#        status = 200
#        if 'If-None-Match' in self.request.headers and self.request.headers['If-None-Match'].find(etag_actual) >= 0:
#            status = 304
#            html = ''
#        #self.response.headers['Last-Modified'] = 'Fri, 01 Jan 1990 00:00:00 GMT'
#        #self.response.headers['Cache-Control'] = 'public, max-age=2592000'
#        self.response.headers['Cache-Control'] = 'public, must-revalidate'
#        self.response.headers['ETag'] = 'w/"%s"' % (etag_actual,)
#        self.response.set_status(status)
#        self.response.headers['Content-Length'] = len(html)
#        self.response.out.write(html)

def gzip(str):
    import StringIO
    import gzip
    out = StringIO.StringIO()
    f = gzip.GzipFile(fileobj=out, mode='w')
    f.write("This is mike number one, isn't this a lot of fun?")
    f.close()
    return out.getvalue()

class EtagExperiment(webapp.RequestHandler):
    def get(self):
        if 'If-None-Match' in self.request.headers:
            status = 304
            headers = { 'Date': 'Tue, 20 Mar 2012 20:07:51 GMT', 'Server': 'Google Frontend' }
        else:
            body = gzip('hello gzipped?')
            status = 200
            headers = { 'Cache-Control' : 'public, must-revalidate',
                        #'Content-Encoding' : 'gzip',
                        #'Content-Length' : '%d' % len(body),
                        #'Content-Type' : 'text/html; charset=utf-8',
                        #'Date' : 'Tue, 20 Mar 2012 20:06:24 GMT',
                        'ETag' : 'w/"0-124427221-0-"',
                        #'Server' : 'Google Frontend',
                        #'Vary' : 'Accept-Encoding',
            }

        #for key in self.response.headers:
        #    del self.response.headers[key]
        for key in headers.keys():
            self.response.headers[key] = headers[key]
        self.response.set_status(status)
        if status == 200:
            self.response.out.write(body)

class DateModifiedExperiment(webapp.RequestHandler):
    def get(self):
        html = 'Checking if caching via If-Modified-Since works<br>%s' % random.random()
        status = 200
        if 'If-Modified-Since' in self.request.headers:
            date = self.request.headers['If-Modified-Since']
            #raise Exception('%s' % date)
            status = 304
            html = ''
        self.response.headers['ETag'] = '"%s"' % ('1234',)
        self.response.headers['Cache-Control'] = 'public, max-age=2592000'
        self.response.headers['Last-Modified'] = 'Fri, 01 Jan 1990 00:00:00 GMT'
        self.response.set_status(status)
        self.response.headers['Content-Length'] = len(html)
        self.response.out.write(html)

application = webapp.WSGIApplication(
    [
        ('/experiment/etag', EtagExperiment),
        ('/experiment/date-modified', DateModifiedExperiment),
    ],
    debug=True)

def main():
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
