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

# Google AppEngine imports
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from models import *
from rst import rst2html
import defs
import request

import utils

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

    def get_tag_counts(self):
        """
        Get tag counts and calculate tag cloud frequencies.
        
        :rtype: list
        :return: list of ``TagCount`` objects, in random order
        """
        tag_counts = Article.get_all_tags()
        result = []
        if tag_counts:
            maximum = max(tag_counts.values())

            for tag, count in tag_counts.items():
                tc = TagCount(tag, count)

                # Determine the popularity of this term as a percentage.

                percent = math.floor((tc.count * 100) / maximum)

                # determine the CSS class for this term based on the percentage

                if percent <= 20:
                    tc.css_class = 'tag-cloud-tiny'
                elif 20 < percent <= 40:
                    tc.css_class = 'tag-cloud-small'
                elif 40 < percent <= 60:
                    tc.css_class = 'tag-cloud-medium'
                elif 60 < percent <= 80:
                    tc.css_class = 'tag-cloud-large'
                else:
                    tc.css_class = 'tag-cloud-huge'
                    
                result.append(tc)

        random.shuffle(result)
        return result

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

    def augment_articles(self, articles, url_prefix, html=True):
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
            if html:
                try:
                    def my_rst2html(markup):
                        markup = markup.replace('\n', '<br>\n')
                        return markup
                    #article.html = rst2html(article.body)
                    article.html = my_rst2html(article.body)
                    article.html = self.handle_custom_tag_mp3(article.html)
                    article.html = self.handle_custom_tag_youtube(article.html)
                    article.html = self.handle_custom_tag_mixcloud(article.html)
                except AttributeError, e:
                    #article.html = 'an error occured performing rst2html()'
                    raise e
            #article.path = '/' + defs.ARTICLE_URL_PATH + '/%s' % article.id
            slug = utils.slugify(article.title)
            article.path = '/%s-%s.html' % (article.id, slug)
            article.url = url_prefix + article.path
            article.comments_count = article.comment_set.count()

    def handle_custom_tag_youtube(self, input):
        import re
        regex = "\[\s*(http://)?(www\.)?youtube\.com/watch\?v=([a-zA-Z0-9-_]+)\s*\]"
        #replace = '<iframe width="425" height="349" src="http://www.youtube.com/embed/\\3" frameborder="0" allowfullscreen></iframe>'
        replace = '<img class="youtube" ytid="\\3" src="http://img.youtube.com/vi/\\3/0.jpg">'
        return re.sub(regex, replace, input)

    def handle_custom_tag_mp3(self, input):
        dropbox_user = "1883230"

        #regex = "\[mp3 +([^\]]+)]"
        regex = "\[([^\]]+mp3)\]"

        repl_link  = "http://dl.dropbox.com/u/%s/sg/\\1" % (dropbox_user)
        repl_swf   = "http://dl.dropbox.com/u/%s/dewplayer-mini.swf" % (dropbox_user)
        repl_flash = "<object width='160' height='18'><embed src='" + repl_swf + "' width='160' height='18' type='application/x-shockwave-flash' flashvars='&mp3=" + repl_link + "' quality='high'></embed></object>"
        repl_dload = "<a href=\"%s\">\\1</a>" % (repl_link)
        repl = "%s %s" % (repl_flash, repl_dload)

        import re
        return re.sub(regex, repl, input)

    def handle_custom_tag_mixcloud(self, input):
        dropbox_user = "1883230"

        #regex = "\[mp3 +([^\]]+)]"
        regex = "\[\s*(http://)?(www.)?mixcloud.com/([a-zA-Z0-9-]+)/([a-zA-Z0-9-]+)/?\s*\]"

        replace  = '<object height="400" width="400"><param name="movie" value="http://www.mixcloud.com/media/swf/player/mixcloudLoader.swf?feed=http%3A%2F%2Fwww.mixcloud.com%2F\\3%2F\\4%2F&amp;embed_uuid=3b4627b1-74e1-43ef-bc52-717acca644d4&amp;embed_type=widget_standard"><param name="allowFullScreen" value="true"><param name="allowscriptaccess" value="always"><embed src="http://www.mixcloud.com/media/swf/player/mixcloudLoader.swf?feed=http%3A%2F%2Fwww.mixcloud.com%2F\\3%2F\\4%2F&amp;embed_uuid=3b4627b1-74e1-43ef-bc52-717acca644d4&amp;embed_type=widget_standard" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true" height="400" width="400"></object>'

        import re
        return re.sub(regex, replace, input)

    def render_articles(self,
                        articles,
                        request,
                        recent,
                        template_name='articles.html',
                        additional_template_variables = None):
        url_prefix = 'http://' + request.environ['SERVER_NAME']
        port = request.environ['SERVER_PORT']
        if port:
            url_prefix += ':%s' % port

        self.augment_articles(articles, url_prefix)
        self.augment_articles(recent, url_prefix, html=False)

        last_updated = datetime.datetime.now()
        if articles:
            last_updated = articles[0].published_when

        blog_url = url_prefix
        tag_path = '/' + defs.TAG_URL_PATH
        tag_url = url_prefix + tag_path
        date_path = '/' + defs.DATE_URL_PATH
        date_url = url_prefix + date_path
        media_path = '/' + defs.MEDIA_URL_PATH
        media_url = url_prefix + media_path

        template_variables = {'blog_name'    : defs.BLOG_NAME,
                              'canonical_blog_url' : defs.CANONICAL_BLOG_URL,
                              'blog_owner'   : defs.BLOG_OWNER,
                              'articles'     : articles,
                              'tag_list'     : self.get_tag_counts(),
                              'date_list'    : self.get_month_counts(),
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
                              'recent'       : recent}

        if additional_template_variables:
            template_variables.update(additional_template_variables)
        return self.render_template(template_name, template_variables)

    def setup_template_variables(self, template_variables):
        pass
    
    def get_recent(self):
        """
        Get up to ``defs.TOTAL_RECENT`` recent articles.

        :rtype: list
        :return: list of recent ``Article`` objects
        """
        articles = Article.published()

        total_recent = min(len(articles), defs.TOTAL_RECENT)
        if articles:
            recent = articles[0:total_recent]
        else:
            recent = []

        return recent

class FrontPageHandler(AbstractPageHandler):
    """
    Handles requests to display the front (or main) page of the blog.
    """
    def get(self):
        articles = Article.published()
        if len(articles) > defs.MAX_ARTICLES_PER_PAGE:
            articles = articles[:defs.MAX_ARTICLES_PER_PAGE]

        self.response.out.write(self.render_articles(articles,
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
        article = Article.get(int(id))
        if article:
            template = 'articles.html'
            articles = [article]
            more = None
        else:
            template = 'not-found.html'
            articles = []
        additional_template_variables = {'single_article': True}
        self.response.out.write(self.render_articles(articles,
                                                     self.request,
                                                     self.get_recent(),
                                                     template,
                                                     additional_template_variables))

class ArchivePageHandler(AbstractPageHandler):
    """
    Handles requests to display the list of all articles in the blog.
    """
    def get(self):
        articles = Article.published()
        self.response.out.write(self.render_articles(articles,
                                                     self.request,
                                                     [],
                                                     'archive.html'))

class RSSFeedHandler(AbstractPageHandler):
    """
    Handles request for an RSS2 feed of the blog's contents.
    """
    def get(self):
        articles = Article.published()
        self.response.headers['Content-Type'] = 'text/xml'
        self.response.out.write(self.render_articles(articles,
                                                     self.request,
                                                     [],
                                                     'rss2.xml'))

class AddCommentHandler(AbstractPageHandler):
    def post(self, article_id):
        article_id = int(article_id)
        author = cgi.escape(self.request.get('author'))
        text = cgi.escape(self.request.get('text'))
        article = Article.get(article_id)
        
        comment = Comment(article=article, author=author, text=text)
        
        comment.save()
        self.redirect('/%d-a-comment-added' % (article_id))

class NotFoundPageHandler(AbstractPageHandler):
    """
    Handles pages that aren't found.
    """
    def get(self):
        self.response.out.write(self.render_articles([],
                                                     self.request,
                                                     [],
                                                     'not-found.html'))

# -----------------------------------------------------------------------------
# Main program
# -----------------------------------------------------------------------------

from google.appengine.ext.webapp import template
template.register_template_library('tags.mytags')

webapp.template.register_template_library('my_tags')

application = webapp.WSGIApplication(
    [('/', FrontPageHandler),
     ('/tag/([^/]+)/*$', ArticlesByTagHandler),
     ('/date/(\d\d\d\d)-(\d\d)/?$', ArticlesForMonthHandler),
     ('/(\d+).*$', SingleArticleHandler),
     ('/archive/?$', ArchivePageHandler),
     ('/rss/?$', RSSFeedHandler),
     ('/comment/add/(\d+)$', AddCommentHandler),
     ('/.*$', NotFoundPageHandler),
     ],

    debug=True)

def main():
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
