import urllib
import datetime
import simplejson as json
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

# todo: consider handling over quota exc
def send_mail_to_admin_about_new_comment(path, comment, client_ip):
    url = 'http://%s' % path

    body='''
%s (%s)

%s

%s''' % (comment['name'], client_ip, comment['text'], url)

    from google.appengine.api import mail
    mail.send_mail(sender='zeencd@gmail.com',
                   to='zeencd@gmail.com',
                   subject='[SG.com] New comment at %s' % path,
                   body=body)


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

def format_now_rfc():
    # return string like 'Wed, 22 Oct 2008 10:52:40 GMT'
    from wsgiref.handlers import format_date_time
    from time import mktime
    now = datetime.datetime.now()
    stamp = mktime(now.timetuple())
    return format_date_time(stamp)

class RestfulHandler(webapp.RequestHandler):
    @handle_exceptions
    @allow_xss
    def get(self, path):
        self.do_fetch(self.__class__.filter_path(path))

    @handle_exceptions
    @allow_xss
    def post(self, path):
        self.do_append(self.__class__.filter_path(path))


    @classmethod
    def filter_path(cls, path):
        # try to remove leading 'WWW'
        path_low = path.lower()
        www_pfx = 'www.'
        if path_low.startswith('www.') and len(path_low) > len(www_pfx):
            path = path[len(www_pfx) : ]
        return path

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
        """ append a comment to comment set """

        return_url = self.request.get('return')
        if return_url:
            assert False, 'this functionality is disabled now'
            def get_param(name):
                value = self.request.get('name')
                value = value.strip() if value is not None else ''
                if not value:
                    raise Exception('error: param %s not specified' % name)
                return value

            new_comment = {
                'name': get_param('name'),
                'text': get_param('text'),
                'date': format_now_rfc(),
            }
        else:
            ct = self.request.headers['Content-Type']
            # do not specify CT other than formencoded because it leads to method OPTIONS used by Firefox
            # by some reason no POST request follows further
            assert 'application/x-www-form-urlencoded' in ct

            json_str = urllib.unquote_plus(self.request.body)
            if json_str[-1] == '=':
                json_str = json_str[0:-1] # remove that fucking trailing '='

            data = json.loads(json_str)

            mandatory_keys = [ 'name', 'text' ]
            for key in mandatory_keys:
                value = data.get(key, '').strip()
                if not value:
                    raise Exception('error: param %s not specified' % key)

            new_comment = {
                'name': data['name'],
                'text': data['text'],
                'date': format_now_rfc(),
                }

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

        send_mail_to_admin_about_new_comment(path, new_comment, self.request.remote_addr)

        if return_url:
            self.redirect(return_url)


def main():
    application = webapp.WSGIApplication([
        ('/comments/(.+)', RestfulHandler),
    ], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
