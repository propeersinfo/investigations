import urllib
import urllib2
import simplejson as json
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

class CommentSet(db.Model):
    # path like 'domain.com/full/path'
    path = db.StringProperty()
    # json encoded list of comments
    json = db.TextProperty()

    @classmethod
    def get_by_path(cls, path):
        return CommentSet.all().filter('path =', path).get()

do_handle_exceptions = False
def handle_exceptions(wrapped):
    def wrapper(self, *args, **kwargs):
        try:
            return wrapped(self, *args, **kwargs)
        except Exception, e:
            self.response.set_status(500)
            self.response.out.write('Internal error occured: %s' % e)
    return wrapper if do_handle_exceptions else wrapped


# a decorator allowing XSS
def allow_xss(wrapped):
    def wrapper(self, *args, **kwargs):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        return wrapped(self, *args, **kwargs)
    return wrapper


class RestfulHandler(webapp.RequestHandler):
    @handle_exceptions
    @allow_xss
    def get(self, path):
        self.do_fetch(path)

    @handle_exceptions
    @allow_xss
    def post(self, path):
        self.do_append(path)

#    def options(self, *args):
#        self.response.headers['Access-Control-Allow-Origin'] = '*'
#        self.response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
#        self.response.headers['Access-Control-Max-Age'] = 1000
#        self.response.headers['Access-Control-Allow-Headers'] = '*'

    def do_fetch(self, path):
        callback = self.request.get('callback')
        entry = CommentSet.get_by_path(path)
        json_str = entry.json if entry else json.dumps([])
        if callback:
            json_str = '%s(%s)' % (callback, json_str)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json_str)

    def do_append(self, path):
        """ update entry or create it on demand """
        return_url = self.request.get('return')
        if return_url:
            new_comment = {
                'name': self.request.get('name'),
                'text': self.request.get('text')
            }
        else:
            ct = self.request.headers['Content-Type']
            # do not specify CT other than formencoded because it leads to method OPTIONS used by Firefox
            # by some reason no POST request follows further
            assert 'application/x-www-form-urlencoded' in ct

            json_str = urllib.unquote_plus(self.request.body)
            if json_str[-1] == '=':
                json_str = json_str[0:-1] # remove that fucking trailing '='

            new_comment = json.loads(json_str)

        assert type(new_comment) == dict
        entry = CommentSet.get_by_path(path)
        if entry:
            comment_list = json.loads(entry.json)
            assert type(comment_list) == list
            comment_list.append(new_comment)
            entry.json = json.dumps(comment_list)
            entry.put()
            #self.response.out.write('an entry updated')
        else:
            comment_list = [ new_comment ]
            entry = CommentSet(path=path, json=json.dumps(comment_list))
            entry.put()
            #self.response.out.write('an entry created')

        if return_url:
            self.redirect(return_url)


def main():
    application = webapp.WSGIApplication([
        ('/comments/(.+)', RestfulHandler),
    ], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
