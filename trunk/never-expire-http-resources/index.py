import time
import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

from static_files import StaticFilesInfo
from static_files import WHERE_STATIC_FILES_ARE_STORED

# Register custom django template tags
template.register_template_library('django_tags')

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

def transmit_file(file, out):
    f = open(file, 'rb')
    try:
        out.write(f.read())
    finally:
        if f: f.close()

class FrontPageHandler(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(template.render('index.html', {}))

class NeverExpireResourceHandler(webapp.RequestHandler):
    def get(self, file_version, file_base, file_ext):
        resource = '%s.%s' % (file_base, file_ext)

        # Some previous version of resource requested - redirect to the right version
        correct_path = StaticFilesInfo.get_resource_path(resource)
        if self.request.path != correct_path:
            self.redirect(correct_path) # todo: response 'moved permanently'?
            return

        self.response.headers['Content-Type'] = CONTENT_TYPES.get(file_ext, DEFAULT_CONTENT_TYPE)
        # Handle future non-forced page reloads
        self.response.headers['Expires'] = NEVER_AS_DATE
        self.response.headers['Cache-Control'] = "max-age=%s, public" % NEVER_AS_SECONDS
        # Handle future forced page reloads (Ctrl+R, F5)
        self.response.headers['Last-Modified'] = ANY_DATE_IN_THE_PAST

        if 'If-Modified-Since' in self.request.headers:
            # This flag means the client has its own copy of the resource
            # and we may not return it. We won't.
            # Just set the response code to Not Changed.
            self.response.set_status(304)
        else:
            time.sleep(1) # todo: just making resource loading process noticeable
            abs_file = os.path.join(os.path.split(__file__)[0], WHERE_STATIC_FILES_ARE_STORED, resource)
            transmit_file(abs_file, self.response.out)

application = webapp.WSGIApplication(
    [('^/$', FrontPageHandler),
     # Example /static/123456/image.jpg
     ('/'+WHERE_STATIC_FILES_ARE_STORED+'/(\d+)/(.+)\.(.+)', NeverExpireResourceHandler),
    ],
    debug=True)

if __name__ == '__main__':
    util.run_wsgi_app(application)