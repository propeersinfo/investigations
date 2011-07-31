# $Id$

"""
Google App Engine Script that handles display of the published
items in the blog.
"""

__docformat__ = 'restructuredtext'

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from docutils import core, nodes, parsers

import logging
import os
import cgi
import sys
import math
import random
import datetime
import re

# Google AppEngine imports
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from models import *
from rst import rst2html
import defs
import request
import utils
import simplemarkup
from paging import PagedQuery, PageInfoBase, PageInfo, EmptyPageInfo, SinglePageInfo, NoPagingPageInfo
from user import UserInfo

from google.appengine.ext.webapp import template
template.register_template_library('my_tags')


# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------

class DateCount(object):
    """
    Convenience class for storing and sorting year/month counts.
    """
    def __init__(self, date, count):
        self.date = date
        self.count = count

    def __cmp__(self, other):
        return cmp(self.date, other.date)

    def __hash__(self):
        return self.date.__hash__()

    def __str__(self):
        return '%s(%d)' % (self.date, self.count)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, str(self))

class TagCount(object):
    """
    Convenience class for storing and sorting tags and counts.
    """
    def __init__(self, tag, count):
        self.css_class = ""
        self.count = count
        self.tag = tag

class AbstractPageHandler(request.BlogRequestHandler):
    """
    Abstract base class for all handlers in this module. Basically,
    this class exists to consolidate common logic.
    """

#    def get_tag_counts(self):
#        """
#        Get tag counts and calculate tag cloud frequencies.
#
#        :rtype: list
#        :return: list of ``TagCount`` objects, in random order
#        """
#        tag_counts = Article.get_all_tags()
#        result = []
#        if tag_counts:
#            maximum = max(tag_counts.values())
#
#            for tag, count in tag_counts.items():
#                tc = TagCount(tag, count)
#
#                # Determine the popularity of this term as a percentage.
#
#                percent = math.floor((tc.count * 100) / maximum)
#
#                # determine the CSS class for this term based on the percentage
#
#                if percent <= 20:
#                    tc.css_class = 'tag-cloud-tiny'
#                elif 20 < percent <= 40:
#                    tc.css_class = 'tag-cloud-small'
#                elif 40 < percent <= 60:
#                    tc.css_class = 'tag-cloud-medium'
#                elif 60 < percent <= 80:
#                    tc.css_class = 'tag-cloud-large'
#                else:
#                    tc.css_class = 'tag-cloud-huge'
#
#                result.append(tc)
#
#        random.shuffle(result)
#        return result

    def get_month_counts(self):
        """
        Get date counts, sorted in reverse chronological order.
        
        :rtype: list
        :return: list of ``DateCount`` objects
        """
        hash = Article.get_all_datetimes()
        datetimes = hash.keys()
        date_count = {}
        for dt in datetimes:
            just_date = datetime.date(dt.year, dt.month, 1)
            try:
                date_count[just_date] += hash[dt]
            except KeyError:
                date_count[just_date] = hash[dt]

        dates = date_count.keys()
        dates.sort()
        dates.reverse()
        return [DateCount(date, date_count[date]) for date in dates]

    def augment_articles(self, articles, url_prefix, produce_html=True):
        """
        Augment the ``Article`` objects in a list with the expanded
        HTML, the path to the article, and the full URL of the article.
        The augmented fields are:

        - ``html``: the optionally expanded HTML
        - ``path``: the article's path
        - ``url``: the full URL to the article
        
        :Parameters:
            articles : list
                list of ``Article`` objects to be augmented

            url_prefix : str
                URL prefix to use when constructing full URL from path
                
            html : bool
                ``True`` to generate HTML from each article's RST
        """
        for article in articles:
            if produce_html:
                #article.html = rst2html(article.body)
                article.html = simplemarkup.markup2html(article.body)
            article.path = utils.get_article_path(article)
            article.url = url_prefix + article.path
            article.guid = url_prefix + utils.get_article_guid(article)
            article.comments_count = article.comment_set.count()
            article.published_class = 'draft' if article.draft else 'published'
            article.comments = [] # article.comment_set cannot be adjusted
            for comment in article.comment_set:
                comment.html = simplemarkup.markup2html(markup_text=comment.text,
                                                        rich_markup=False,
                                                        recognize_links=comment.blog_owner)
                article.comments.append(comment)

    def render_articles(self,
                        page_info,
                        request,
                        recent,
                        template_name='articles.html',
                        additional_template_variables = None):
        if not isinstance(page_info, PageInfoBase):
            raise Exception("Use 'page_info' instead of 'articles'; actual = %s" % type(page_info.articles))

        articles = page_info.articles

        url_prefix = 'http://' + request.environ['SERVER_NAME']
        port = request.environ['SERVER_PORT']
        if port:
            url_prefix += ':%s' % port

        self.augment_articles(articles, url_prefix)
        self.augment_articles(recent, url_prefix, produce_html=False)

        last_updated = last_updated = (articles[0].published_date) if (articles) else (datetime.datetime.now())

        blog_url = url_prefix
        tag_path = '/' + defs.TAG_URL_PATH
        tag_url = url_prefix + tag_path
        date_path = '/' + defs.DATE_URL_PATH
        date_url = url_prefix + date_path
        media_path = '/' + defs.MEDIA_URL_PATH
        media_url = url_prefix + media_path

        user_info = UserInfo(request)

        template_variables = {
            'blog_name'    : defs.BLOG_NAME,
            'canonical_blog_url' : defs.CANONICAL_BLOG_URL,
            'blog_owner'   : defs.BLOG_OWNER,
            'current_path' : request.path,
            'articles'     : articles,
            'tag_list'     : None, #self.get_tag_counts(),
            'date_list'    : None, #self.get_month_counts(),
            'version'      : '0.3',
            'last_updated' : last_updated,
            'blog_path'    : '/',
            'blog_url'     : blog_url,
            'archive_path' : '/' + defs.ARCHIVE_URL_PATH,
            'tag_path'     : tag_path,
            'tag_url'      : tag_url,
            'date_path'    : date_path,
            'date_url'     : date_url,
            'rss2_path'    : '/' + defs.RSS2_URL_PATH,
            'recent'       : recent,
            'user_info'    : user_info,
            'blog_owner_name' : defs.BLOG_OWNER,
            'comment_author'  : utils.get_unicode_cookie(self.request, 'comment_author', ''),
            'prev_page_url'   : page_info.prev_page_url,
            'next_page_url'   : page_info.next_page_url
        }

        if additional_template_variables:
            template_variables.update(additional_template_variables)

        return self.render_template(template_name, template_variables)

    def get_recent(self):
        return []

class FrontPageHandler(AbstractPageHandler):
    """
    Handles requests to display the front (or main) page of the blog.
    """
    def get(self, page_num = 1):
        page_num = int(page_num)
        
        #articles = Article.published()
        #if len(articles) > defs.MAX_ARTICLES_PER_PAGE:
        #    articles = articles[:defs.MAX_ARTICLES_PER_PAGE]

        q = Article.query_all() if users.is_current_user_admin() else Article.query_published()
        page_info = PageInfo(PagedQuery(q, defs.MAX_ARTICLES_PER_PAGE),
                             page_num,
                             "/page%d",
                             "/")
        #raise Exception("page_info: %s" % type(page_info))
        self.response.out.write(self.render_articles(page_info,
                                                     self.request,
                                                     self.get_recent()))

class ArticlesByTagHandler(AbstractPageHandler):
    """
    Handles requests to display a set of articles that have a
    particular tag.
    """
    def get(self, tag):
        articles = Article.all_for_tag(tag)
        self.response.out.write(self.render_articles(articles,
                                                     self.request,
                                                     self.get_recent()))

class ArticlesForMonthHandler(AbstractPageHandler):
    """
    Handles requests to display a set of articles that were published
    in a given month.
    """
    def get(self, year, month):
        articles = Article.all_for_month(int(year), int(month))
        self.response.out.write(self.render_articles(articles,
                                                     self.request,
                                                     self.get_recent()))

class SingleArticleHandler(AbstractPageHandler):
    """
    Handles requests to display a single article, given its unique ID.
    Handles nonexistent IDs.
    """
    def get(self, id):
        id = int(id)
        article = Article.get(id)

        if article:
            true_path = utils.get_article_path(article)
            if self.request.path != true_path:
                self.redirect(true_path, permanent=True)
                return

        template = self.get_template_file(article)
        additional_template_variables = {'single_article': article}
        self.response.out.write(self.render_articles(SinglePageInfo(article),
                                                     self.request,
                                                     self.get_recent(),
                                                     template,
                                                     additional_template_variables))
    def get_template_file(self, article):
        if not article:
            return '404.html'
        elif article.draft and not users.is_current_user_admin():
            return '403.html'
        else:
            return 'articles.html'

class ArchivePageHandler(AbstractPageHandler):
    """
    Handles requests to display the list of all articles in the blog.
    """
    def get(self, page_num):
        page_num = int(page_num) if page_num else 1
        q = Article.query_all() if users.is_current_user_admin() else Article.query_published()
        page_info = PageInfo(PagedQuery(q, defs.MAX_ARTICLES_PER_PAGE_ARCHIVE),
                             page_num,
                             "/archive/%d",
                             "/archive/")
        self.response.out.write(self.render_articles(page_info,
                                                     self.request,
                                                     [],
                                                     'archive.html'))

class RssArticlesHandler(AbstractPageHandler):
    """
    Handles request for an RSS2 feed of the blog's contents.
    """
    def get(self):
        pager = NoPagingPageInfo(PagedQuery(Article.query_published(), defs.MAX_ARTICLES_RSS))
        self.response.headers['Content-Type'] = 'text/xml'
        self.response.out.write(self.render_articles(pager,
                                                     self.request,
                                                     [],
                                                     '../rss-articles.xml'))

class AddCommentHandler(AbstractPageHandler):
    def post(self, article_id):
        article_id = int(article_id)
        article = Article.get(article_id)

        #if True: raise Exception("article_id = %s, article = %s, article.id = %s" % (article_id, article, article.id))

        author = cgi.escape(self.request.get('author')).strip()
        #if author == '' and not users.is_current_user_admin():
        #    author = 'Anonymous'

        comment = Comment(article = article,
                          author = author,
                          text = cgi.escape(self.request.get('text')),
                          blog_owner = users.is_current_user_admin())
        comment.save()
        utils.set_unicode_cookie(self.response, "comment_author", author)
        self.redirect(utils.get_article_path(article))

class NotFoundPageHandler(AbstractPageHandler):
    """
    Handles pages that aren't found.
    """
    def get(self):
        self.response.out.write(self.render_articles(EmptyPageInfo(),
                                                     self.request,
                                                     [],
                                                     '404.html'))

# -----------------------------------------------------------------------------
# Main program
# -----------------------------------------------------------------------------

from google.appengine.ext.webapp import template
template.register_template_library('tags.mytags')

webapp.template.register_template_library('my_tags')

application = webapp.WSGIApplication(
    [('/', FrontPageHandler),
     ('/page(\d+)/?', FrontPageHandler),
     ('/tag/([^/]+)/*$', ArticlesByTagHandler),
     ('/date/(\d\d\d\d)-(\d\d)/?$', ArticlesForMonthHandler),
     ('/(\d+).*$', SingleArticleHandler),
     ('/archive/(\d+)?$', ArchivePageHandler),
     ('/rss/?$', RssArticlesHandler),
     ('/comment/add/(\d+)$', AddCommentHandler),
     ('/.*$', NotFoundPageHandler),
     ],

    debug=True)

def main():
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
