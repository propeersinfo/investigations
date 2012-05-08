import codecs
import os
import re
import urllib
import cgi
import logging
import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import users
from google.appengine.runtime.apiproxy_errors import OverQuotaError
from google.appengine.ext.webapp import template

import clevermarkup
import defs
from userinfo import UserInfo
import utils
import gen_static

class TagHandler(webapp.RequestHandler):
    def get(self, tag_name):
        gen_static.generate_tag_page(tag_name)
        html_file = os.path.join(os.path.dirname(__file__), 'html', 'tag', tag_name)
        html = utils.read_file(html_file)
        self.response.out.write(html)


class ArticleHandler(webapp.RequestHandler):
    def get(self, slug):
        gen_static.generate_article(slug)
        html_file = os.path.join(os.path.dirname(__file__), 'html', slug)
        html = utils.read_file(html_file)
        self.response.out.write(html)


class ArticleListingHandler(webapp.RequestHandler):
    def get(self, page1 = 1):
        if type(page1) == str:
            page1 = int(page1)
        html_file = gen_static.generate_listing(page1)
        html = utils.read_file(html_file)
        self.response.out.write(html)


class RssHandler(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = "text/plain; charset=utf-8"
        html_file = gen_static.generate_rss()
        html = utils.read_file(html_file)
        self.response.out.write(html)


webapp.template.register_template_library('my_tags')

application = webapp.WSGIApplication(
    [
        ('/preview/tag/(.+)', TagHandler),
        ('/preview/', ArticleListingHandler),
        ('/preview/page(\d+)', ArticleListingHandler),
        ('/preview/rss', RssHandler),
        ('/preview/(.+)', ArticleHandler),
    ],
    debug=True)

def main():
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
