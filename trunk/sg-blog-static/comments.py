from StringIO import StringIO
import os
import re
import urllib
import datetime
from wsgiref.handlers import format_date_time

from google.appengine.api import users
import simplejson as json
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db


# todo: consider handling over quota exc

# format an str/unicode json-string as one readable by humans
# because the standard json.sumps() produces all these '\xUUUU'
def pretty_print_json_readable_unicode(json_text):
    def do_level(out, root, level = 0):
        offset = '  ' * level
        offset2 = '  ' * (level+1)
        if type(root) == list:
            out.write('%s[\n' % (offset,))
            for i, item in enumerate(root):
                if i > 0: out.write('%s,\n' % offset)
                do_level(out, item, level+1)
            out.write('\n%s]' % (offset,))
        elif type(root) == dict:
            out.write('%s{\n' % (offset,))
            for i, key in enumerate(root.keys()):
                if i > 0: out.write('%s,\n' % '')
                out.write('%s"%s": ' % (offset2, key))
                do_level(out, root[key], level+1)
            out.write('\n%s}' % offset)
        elif isinstance(root, basestring):
            root = root.replace('"', '\\"').replace('\r', '\\r').replace('\n', '\\n')
            out.write('"%s"' % (root,))
        else:
            raise Exception('unsupported yet type %s' % type(root))

    assert isinstance(json_text, (basestring))
    out = StringIO()
    try:
        do_level(out, json.loads(json_text))
        return out.getvalue()
    finally:
        out.close()

def send_mail_to_admin_about_new_comment(path, comment_system_base_url, comment, client_ip):
    url = 'http://%s' % path
    edit_url = '%s/comments/edit/%s' % (comment_system_base_url, path)

    body='''
%s (%s)

%s

%s
%s''' % (comment['name'], client_ip, comment['text'], url, edit_url)

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
    from time import mktime
    now = datetime.datetime.utcnow()
    stamp = mktime(now.timetuple())
    return format_date_time(stamp)

def filter_path(path):
    # try to remove leading 'WWW'
    path_low = path.lower()
    www_pfx = 'www.'
    if path_low.startswith('www.') and len(path_low) > len(www_pfx):
        path = path[len(www_pfx) : ]
    return path

#def render_template(template_name, variables):
#    env = Environment(loader=FileSystemLoader(['comments']), cache_size=0)
#    tpl = env.get_template(template_name)
#    return tpl.render(variables)

def render_template(template_name, template_vars):
    from google.appengine.ext.webapp import template
    template_path = os.path.join(os.path.dirname(__file__), 'themes', 'comments', template_name)
    text = template.render(template_path, template_vars)
    #raise Exception('google template returns %s' % type(text))
    return text

class EditHandler(webapp.RequestHandler):
    def get(self, path):
        path = filter_path(path)
        entry = CommentSet.get_by_path(path)
        if entry:
            text = entry.json
            def unicode_decoder(m):
                code = int(m.group(1), base=16)
                assert type(code) == int
                res = unichr(code)
                #raise Exception('res: %s' % type(res))
                return '%s' % res
            text = re.sub('\\\u([0-9a-fA-F]{4})', unicode_decoder, text)
            text = pretty_print_json_readable_unicode(text)

            assert isinstance(text, basestring)
            self.response.headers['Content-Type'] = 'text/html; charset=utf-8'
            #self.response.out.write('<p>Comments has been found for path %s' % (path))
            #self.response.out.write('<p><textarea cols=80 rows=30 style="width:100%%;">%s</textarea>' % text)
            tpl_vars = {
                'json': text,
                'path': path,
                'is_admin': users.is_current_user_admin(),
                'logout_url': users.create_logout_url(self.request.path)
            }
            self.response.out.write(render_template('edit.html', tpl_vars))
        else:
            self.response.set_status(404)
            self.response.out.write('no comments found for path %s' % path)

    def post(self, path):
        path = filter_path(path)
        json_text = self.request.get('json')
        json_obj = json.loads(json_text)
        #raise Exception('%s' % (json_obj,))
        entry = CommentSet.get_by_path(path)
        if entry:
            entry.json = json.dumps(json_obj)
            entry.put()
            self.redirect('/comments/edit/%s' % path)
        else:
            self.response.set_status(404)
            self.response.out.write('No comments fount for the path')

class RestfulHandler(webapp.RequestHandler):
    @handle_exceptions
    @allow_xss
    def get(self, path):
        self.do_fetch(filter_path(path))

    @handle_exceptions
    @allow_xss
    def post(self, path):
        self.do_append(filter_path(path))


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

        send_mail_to_admin_about_new_comment(path, self.request.host_url, new_comment, self.request.remote_addr)

        if return_url:
            self.redirect(return_url)


def main():
    application = webapp.WSGIApplication([
        ('/comments/edit/(.+)', EditHandler),
        ('/comments/(.+)', RestfulHandler),
    ], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
