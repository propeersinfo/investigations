# -*- coding: utf-8 -*-

import os
import re
import unicodedata
import Cookie
import datetime

import defs
import models

class PageLoadTime():
    def __init__(self):
        self.start_time = datetime.datetime.now()
    def print_time(self, out):
        delta = datetime.datetime.now() - self.start_time
        out.write('<center><p>Page generated for %d:%03d<p>&nbsp;</center>' % (delta.seconds, delta.microseconds/1000))

# Examples:
# http://localhost/_ah/admin/datastore/edit?key=ahRkZXZ-c292aWV0cmFyZWdyb292ZXIPCxIHQXJ0aWNsZRjh1AEM&kind=Article&next=http%3A//localhost/_ah/admin/datastore%3Fkind%3DArticle
# https://appengine.google.com/datastore/edit?app_id=sovietraregroove&version_id=1.357588515741945103&key=ahBzb3ZpZXRyYXJlZ3Jvb3Zlcg8LEgdBcnRpY2xlGPO7AQw
def get_ds_object_edit_link(ds_object):
    key = ds_object.key()
    app_id = 'sovietraregroove'
    if defs.PRODUCTION:
        s = 'https://appengine.google.com/datastore/edit?app_id=%s&version_id=%s&key=%s' % (app_id, defs.APP_VERSION, key)
    else:
        s = '%s/_ah/admin/datastore/edit?key=%s&kind=Article' % (defs.CANONICAL_BLOG_URL, key)
    return s

def slugify(s):
  if type(s) == str:
    s = unicode(s)
  s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').lower()
  s = re.sub("[']", '', s)                        # remove some chars
  s = re.sub('[^a-zA-Z0-9-]+', '-', s)            # replace the rest with '-'
  s = re.sub('--+', '-', s)                       # eliminate '--'
  s = s.strip('-')
  return s

def get_article_path(article):
  #return '/%s-%s.html' % (article.id, slugify(article.title))
  slug = models.Slug.get_default_slug_for_article(article)
  return '/%s' % (slug.slug)

def get_article_url(article):
  return defs.CANONICAL_BLOG_URL + get_article_path(article)

def get_article_guid(article):
  return '/article/%s' % (article.id)
    
def set_unicode_cookie(response, key, value):
  c = Cookie.SimpleCookie()
  c[key] = value.encode('unicode-escape')
  c[key]["expires"] = "Sun, 31-May-2020 23:59:59 GMT"
  c[key]["path"] = "/"
  response.headers.add_header('Set-Cookie', c[key].OutputString())
  
def get_unicode_cookie(request, key, default_value):
  def unescape(s):
    m = re.match(r'^"(.*)"$', s)
    s = m.group(1) if m else s
    return s.replace("\\\\", "\\")
  if request.cookies.has_key(key):
    return unescape(request.cookies[key]).decode('unicode-escape')
  else:
    return default_value


def read_file(file):
    full = os.path.join(os.path.split(__file__)[0], file)
    return open(full).read()

def send_mail_to_admin_about_new_comment(comment):
    from google.appengine.api import mail
    mail.send_mail(sender='zeencd@gmail.com',
                   to='zeencd@gmail.com',
                   subject='New comment in "%s"' % comment.article.title,
                   body='''
Comment author: %s

Coment text: %s

Blog post: %s
''' % (comment.author, comment.text, get_article_url(comment.article)))

class TimePeriod():
    def __init__(self, seconds):
        self.__seconds = seconds
    def seconds(self):
        return self.__seconds

# Usage: utils.hours(1).seconds()
def hours(hours):
    tp = TimePeriod(hours * 60 * 60)
    return tp
    
if __name__ == '__main__':
    titles = [ u'About the cat / Про кота (1985)', u'A dear boy (1974) - Part 1', u'Theme from Rocky\'s cover', u'75 / ВИА 75 (1979)' ]
    for t in titles:
        print slugify(t)

def assert_type(object, expected_type):
    if not isinstance(object, expected_type):
        raise Exception('Expected type: %s. Actual: %s' % (expected_type, type(object)))
