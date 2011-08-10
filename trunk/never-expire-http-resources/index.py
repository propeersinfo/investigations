import time
import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import memcache

# register custom django template tags
from google.appengine.ext.webapp import template
template.register_template_library('django_tags')

def dev_server():
    return os.environ.get('SERVER_SOFTWARE','').lower().find('development') >= 0

def transmit_file(file, out):
    f = open(file, 'rb')
    try:
        out.write(f.read())
    finally:
        if f: f.close()

class StaticFilesInfo():
    @classmethod
    def get(cls):
        info = memcache.get(cls.__name__)
        if info is None:
            info = cls.__grab_info()
            time = 5 if dev_server() else 0
            memcache.set(cls.__name__, info, time) # store it as long as possible
        return info
    @classmethod
    def __grab_info(cls):
        dir = os.path.join(os.path.split(__file__)[0], 'pseudo-static')
        hash = {}
        for file in os.listdir(dir):
            abs_file = os.path.join(dir, file)
            hash[file] = int(os.path.getmtime(abs_file))
        return hash

class FrontPageHandler(webapp.RequestHandler):
    def get(self):
        template_vars = {
            'static_files_info' : StaticFilesInfo.get()
        }
        self.response.headers['Content-Type'] = 'text/html'
        #self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(template.render('blog.html', template_vars))

CONTENT_TYPES = {
    'jpeg': 'image/jpeg',
    'jpg':  'image/jpeg',
    'swf':  'application/x-shockwave-flash',
    'html': 'text/html',
    'txt':  'text/plain',
}
DEFAULT_CONTENT_TYPE = 'binary/octet-stream'

NEVER_AS_SECONDS = 180 * 24 * 60 * 60 # 180 days
NEVER_AS_DATE = 'Fri, 30 Oct 2050 14:19:41 GMT'
ANY_DATE_IN_THE_PAST = 'Fri, 01 Jan 1990 00:00:00 GMT'

def headers2str(headers):
    s = ''
    for key in headers.keys():
        s += "%s: %s\n" % (key, headers[key])
    return s

class PseudoStaticHandler(webapp.RequestHandler):
    def get(self, file_version, base, ext):
        file_version = int(file_version)
        sub_path = '%s.%s' % (base, ext)
        content_type = CONTENT_TYPES.get(ext, DEFAULT_CONTENT_TYPE)
        self.response.headers['Content-Type'] = content_type
        #del self.response.headers['Expires']
        self.response.headers['Expires'] = NEVER_AS_DATE
        self.response.headers['Cache-Control'] = "max-age=%s, public" % NEVER_AS_SECONDS
        self.response.headers['Last-Modified'] = ANY_DATE_IN_THE_PAST
        #etag = '"%s%s"' % (sub_path,file_version)
        #etag = hashlib.sha1(etag).hexdigest()
        #self.response.headers['ETag'] = etag
        abs_file = os.path.join(os.path.split(__file__)[0], 'pseudo-static', sub_path)
        #self.response.out.write('sub_path: %s' % abs_file)

#        self.response.headers['Content-Type'] = "text/plain"
#        self.response.out.write("Request headers:\n%s\n" % headers2str(self.request.headers))
#        self.response.out.write("Response headers:\n%s\n" % headers2str(self.response.headers))
#        return

        serve = True
        if 'If-Modified-Since' in self.request.headers:
            serve = False

#        if 'If-None-Match' in self.request.headers:
#            etags = [x.strip('" ') for x in self.request.headers['If-None-Match'].split(',')]
#            if etag in etags:
#                serve = False

        if serve:
            time.sleep(1)
            transmit_file(abs_file, self.response.out)
        else:
            self.response.set_status(304)

application = webapp.WSGIApplication(
    [('^/$', FrontPageHandler),
     ('/pseudo-static/(\d+)/(.+)\.(.+)', PseudoStaticHandler),
     ],

    debug=True)

def main():
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()