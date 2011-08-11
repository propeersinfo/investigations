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
#import simplemarkup as markup
import clevermarkup as markup
from paging import PagedQuery, PageInfoBase, PageInfo, EmptyPageInfo, SinglePageInfo, NoPagingPageInfo
from userinfo import UserInfo

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
            if article:
                if produce_html:
                    #article.html = rst2html(article.body)
                    article.html = 'article.html is not available anymore'
                    article.complex_html = markup.markup2html(article.body, for_comment=False, article_id=article.id)
                article.path = utils.get_article_path(article)
                article.tag_objects = article.get_tag_objects()
                article.url = url_prefix + article.path
                article.guid = url_prefix + utils.get_article_guid(article)
                article.comments_count = article.comment_set.count()
                article.published_class = 'draft' if article.draft else 'published'
                #article.title = cgi.escape(article.title)
                self.augment_comments_for(article)

    def augment_comments_for(self, article):
        comments = []
        for comment in Comment.get_for_article(article):
            comment.html = markup.markup2html(markup_text=comment.text,
                                              for_comment=True,
                                              rich_markup=False,
                                              recognize_links=comment.blog_owner)
            comment.repliable = (comment.id == comment.replied_comment_id)
            comments.append(comment)
        article.comments = comments
    
#    def augment_comments_for(self, article):
#        comments = []
#        for comment in article.comment_set:
#            comment.html = markup.markup2html(markup_text=comment.text,
#                                                    rich_markup=False,
#                                                    recognize_links=comment.blog_owner)
#            comments.append(comment)
#        article.comments = comments

#    def _augment_comments_for(self, article):
#        class Group(list):
#            def __init__(self, comment):
#                super(list, self).__init__()
#                self.id = comment.id
#                self.append(comment)
#            def __hash__(self):
#                return self.id
#        hash = {}
#        groups = []
#        for comment in article.comment_set:
#            comment.html = markup.markup2html(markup_text=comment.text,
#                                                    rich_markup=False,
#                                                    recognize_links=comment.blog_owner)
#            if comment.replied_comment and hash.has_key(comment.replied_comment.id):
#                #raise Exception("adding to hash")
#                hash[comment.replied_comment.id].append(comment)
#            else:
#                gr = Group(comment)
#                hash[comment.id] = gr
#                groups.append(gr)
#        article.comments = [] # article.comment_set cannot be adjusted
#        for gr in groups:
#            article.comments.extend(gr)
#        #raise Exception(len(article.comments))

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

        #last_updated = last_updated = (articles[0].published_date) if (articles) else (datetime.datetime.now())

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
            'current_path' : cgi.escape(request.path),
            'articles'     : articles,
            'tag_list'     : None, #self.get_tag_counts(),
            'date_list'    : None, #self.get_month_counts(),
            'version'      : '0.3',
            #'last_updated' : last_updated,
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
            'next_page_url'   : page_info.next_page_url,
            'tag_cloud'       : ArticleTag.create_region_tag_cloud(),
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
        self.response.out.write(self.render_articles(page_info,
                                                     self.request,
                                                     self.get_recent()))

class ArticlesByTagHandler(AbstractPageHandler):
    """
    Handles requests to display a set of articles that have a
    particular tag.
    """
    def get(self, tag_name, page_num = 1):
        page_num = int(page_num)
        q = Article.query_for_tag_name(tag_name)
        paged_query = PagedQuery(q, defs.MAX_ARTICLES_PER_PAGE)
        page_info = PageInfo(paged_query,
                             page_num,
                             '/tag/' + tag_name + '/page%d',
                             '/tag/' + tag_name + '/')
        tpl_vars = {
            'paging_title' : '%s blog posts tagged &ldquo;%s&rdquo;' % (paged_query.count(), tag_name)
        }
        self.response.out.write(self.render_articles(page_info,
                                                     self.request,
                                                     self.get_recent(),
                                                     additional_template_variables=tpl_vars))

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

        response_code, template = self.get_code_and_template(article)
        self.response.set_status(response_code)
        additional_template_variables = {'single_article': article}
        self.response.out.write(self.render_articles(SinglePageInfo(article),
                                                     self.request,
                                                     self.get_recent(),
                                                     template,
                                                     additional_template_variables))
    def get_code_and_template(self, article):
        if not article:
            return 404, '404.html'
        elif article.draft and not users.is_current_user_admin():
            return 403, '403.html'
        else:
            return 200, 'articles.html'

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
    def get_replied_comment_id(self):
        str = self.request.get('reply-to').strip()
        if str:
            c = Comment.get(int(str))
            if c: return c.id
        return None

    def post(self, article_id):
        article_id = int(article_id)
        article = Article.get(article_id)

        author = cgi.escape(self.request.get('author')).strip()
        #if author == '' and not users.is_current_user_admin():
        #    author = 'Anonymous'

        comment = Comment(article = article,
                          author = author,
                          text = cgi.escape(self.request.get('text')),
                          blog_owner = users.is_current_user_admin(),
                          replied_comment_id = self.get_replied_comment_id())
        comment.save()
        utils.set_unicode_cookie(self.response, "comment_author", author)
        utils.send_mail_to_admin_about_new_comment(comment)
        self.redirect(utils.get_article_path(article))

class NotFoundPageHandler(AbstractPageHandler):
    def get(self):
        self.response.set_status(404)
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
     ('/tag/([^/]+)/?$', ArticlesByTagHandler),
     ('/tag/([^/]+)/page(\d+)/?$', ArticlesByTagHandler),
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
