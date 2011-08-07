import os
import re
import unicodedata
import urllib
import Cookie
from google.appengine.api import mail

def slugify(s):
  s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').lower()
  s = re.sub("[']", '', s)                        # remove some chars
  s = re.sub('[^a-zA-Z0-9-]+', '-', s).strip('-') # replace the rest with '-'
  return s

def get_article_path(article):
  return '/%s-%s.html' % (article.id, slugify(article.title))
    
def get_article_guid(article):
  return '/%s.html' % (article.id)
    
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
    mail.send_mail(sender='zeencd@gmail.com',
                   to='zeencd@gmail.com',
                   subject='New comment in "%s"' % comment.article.title,
                   body='''
Author: %s

Text: %s

Address: %s
''' % (comment.author, comment.text, get_article_path(comment.article)))