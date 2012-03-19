import re
import cgi
import random
import urllib2
import google.appengine.ext.webapp.template as tpl

from typographus import Typographus

import defs

register = tpl.create_template_register()


def link(url):
  display = url
  display = re.sub('^mailto:\s*', '', display)
  return '<a href="%s">%s</a>' % (url, display)
register.simple_tag(link)

# print a tag
def blog_tag(blog_tag_name, blog_tag_title = None):
  if not blog_tag_title:
    blog_tag_title = blog_tag_name
  return '<a href="/tag/%s">%s</a>' % (blog_tag_name, blog_tag_title)
register.simple_tag(blog_tag)


# print a tag with its usage count
def blog_tag_cnt(tag_cloud, blog_tag_name, blog_tag_title = None):
  #raise Exception('%s' % type(tag_cloud))
  if not blog_tag_title:
    blog_tag_title = blog_tag_name
  count = tag_cloud.get_tag_usage_count(blog_tag_name)
  if count > 0:
    return '<a href="/tag/%s">%s</a> <span>%s</span>' % (blog_tag_name, blog_tag_title, count)
  else:
    return '%s' % blog_tag_title
register.simple_tag(blog_tag_cnt)


def h2_render(text):
  return '<img src="/font?text=%s">' % cgi.escape(text)
register.simple_tag(h2_render)


def sidebar_link(title, description, url):
    return '<li><a href="%s">%s</a><br>\n<span class="description">%s</span></li>\n' % (url, title, description.lower())
    #return '<li><a href="%s" alt="%s">%s</li>\n' % (url, description, title)
register.simple_tag(sidebar_link)


def typographus(s):
    return Typographus().process(s)
register.simple_tag(typographus)


# return versioned url of a local GAE resource
def static_resource(file):
    ver = defs.APP_VERSION if defs.PRODUCTION else str(random.random())
    return '/static/%s?v=%s' % (file, urllib2.quote(ver, safe=''))
register.simple_tag(static_resource)


@register.filter(name='wld')
def wld(result):
  if result == 1 : return "win"
  if result == 0 : return "loss"
  if result == 0.5 : return "draw"
  return "unknown"


@register.filter(name='typographus')
def typographus(s):
  if not isinstance(s, unicode):
    s = unicode(s)
  return Typographus().process(s)
