# $Id: f06befd2bc4b552d08c2d93836b674baa0dc417e $

"""
Google App Engine Script that handles administration screens for the
blog.
"""

import cgi
from datetime import time
import logging
import urllib

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
import defs

from models import *
import request

import utils
from userinfo import UserInfo

from google.appengine.ext.webapp import template
template.register_template_library('my_tags')

ADMIN_FETCH_MAXIMUM = 10 * 1000

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------

class ShowAdminMainPageHandler(request.BlogRequestHandler):
    def get(self):
        template_vars = {
            'dev_server': defs.PRODUCTION == False
        }
        self.response.out.write(self.render_template('admin-main.html',
                                                     template_vars))

class ManageTags(request.BlogRequestHandler):
    def get(self):
        category_selected = self.request.get('category')

        tags_subset = []
        categories = {}
        for tag in db.Query(ArticleTag).order('name').fetch(ADMIN_FETCH_MAXIMUM):
            categories[tag.category] = categories.get(tag.category, 0) + 1
            if tag.category == category_selected:
                tags_subset.append(tag)
            #self.response.out.write('"%s": "%s",<br>\n' % (tag.name, tag.category))

        template_vars = {
            'tags' : tags_subset,
            'current_category': category_selected,
            'categories': categories,
            'current_path': '%s?category=%s' % (self.request.path, category_selected),
        }
        self.response.out.write(self.render_template('admin-tags.html', template_vars))
    def post(self):
        # update a tag
        tag_name = self.request.get('tag')
        new_category = self.request.get('new_category')
        return_path = self.request.get('return_path')
        assert return_path is not None
        if tag_name and new_category:
            tag = ArticleTag.get_by_name(tag_name)
            if tag:
                tag.category = new_category
                tag.save()
        self.redirect(return_path)

class SetupBasicTags(request.BlogRequestHandler):
    def post(self):
        """
        tags_categorized = {
            'region': 'russia,ukraine,moldova,belarus,'
                       'armenia,azerbaijan,georgia,'
                       'estonia,latvia,lithuania,'
                       'kazakhstan,tajikistan,turkmenistan,uzbekistan,kyrgyzstan,',
            'genre': 'funk,psychedelic,progressive,jazz,disco,electro,shake,',
            'artist': 'melodiya,garanian,alexander zatsepin,',
            'time': '60s,70s,80s,',
        }
        """
        from operablogimport.tags_categorized import tags_categorized
        for tag_name in tags_categorized.keys():
            category = tags_categorized[tag_name]
            tag = ArticleTag.get_by_name(tag_name, create_on_demand=True)
            tag.category = category
            tag.save()

        """
        from operablogimport.tags_categorized import tags_categorized
        for tag in ArticleTag.all().fetch(ADMIN_FETCH_MAXIMUM):
            self.response.out.write("%s: %s\n" % (tag.name, tag.category))
            if tags_categorized.has_key(tag.name):
                tag.category = tags_categorized[tag.name]
                tag.save()
        """

        self.redirect('/admin/')

def empty_table(table):
    if defs.PRODUCTION:
        raise Exception("This code cannot be run on production")
    while True:
        q = db.GqlQuery('SELECT __key__ FROM %s' % table)
        if q.count() <= 0:
            break
        db.delete(q.fetch(200))

class ResetTagCounters(request.BlogRequestHandler):
    def post(self):
        reset_all_tag_counters()
        self.redirect('/admin/')

class EmptyDB(request.BlogRequestHandler):
    def post(self):
        empty_table('Article')
        empty_table('Slug')
        empty_table('Comment')
        empty_table('ArticleTag')
        empty_table('FontRenderCache')
        self.redirect('/admin/')

def reset_all_tag_counters():
    q = ArticleTag.all().filter('counter !=', 0)
    for tag in q.fetch(ADMIN_FETCH_MAXIMUM):
        tag.counter = 0
        tag.save()

def calculate_all_tag_counters():
    q = Article.query_all()
    for article in q.fetch(ADMIN_FETCH_MAXIMUM):
        for tag_key in set(article.tags):
            tag = ArticleTag.get_by_key(tag_key, create_on_demand=True)
            tag.counter += 1
            tag.save()

class RecalculateTagCountersFromArticles(request.BlogRequestHandler):
    def post(self):
        TagCloud.reset()
        reset_all_tag_counters()
        calculate_all_tag_counters()
        self.redirect('/admin/')

class NewArticleHandler(request.BlogRequestHandler):
    """
    Handles requests to create and edit a new article.
    """
    def get(self):
        article = Article(title='-',
                          slug = 'x',
                          body=utils.read_file('new-article.txt'),
                          draft=False)
        user_info = UserInfo(self.request)
        template_vars = {
            'article'   : article,
            'user_info' : user_info,
            'new_article' : True
        }
        self.response.out.write(self.render_template('admin-edit.html',
                                                     template_vars))

class EditArticleHandler(request.BlogRequestHandler):
    """
    Handles requests to edit an article.
    """
    def get(self, id):
        id = int(id)
        article = Article.get(id)
        if not article:
            raise ValueError, 'Article with ID %d does not exist.' % id

        slugs = Slug.get_slugs_for_article(article)
        
        #article.tag_string = ', '.join(article.tags)
        article.tag_string = ', '.join(article.get_tag_names())
        template_vars = {
            'article'  : article,
            'from'     : cgi.escape(self.request.get('from')),
            'tag_cloud' : TagCloud.get(),
            'slugs'    : slugs
        }
        self.response.out.write(self.render_template('admin-edit.html',
                                                     template_vars))

class SaveArticleHandler(request.BlogRequestHandler):
    """
    Handles form submissions to save an edited article.
    """
    def post(self):
        #url_from = cgi.escape(self.request.get('from'))
        url_from = self.request.get('from')
        title = self.request.get('title')
        slug = self.request.get('slug')
        #raise Exception('Slug is %s.' % slug)
        body = self.request.get('content')
        s_id = cgi.escape(self.request.get('id'))
        id = int(s_id) if s_id else None
        tag_names_new = cgi.escape(self.request.get('tags'))
        published_date = cgi.escape(self.request.get('published_date'))
        draft = cgi.escape(self.request.get('draft'))
        if tag_names_new:
            tag_names_new = [t.strip() for t in tag_names_new.split(',')]
        else:
            tag_names_new = []
        tag_objects_new = Article.convert_string_tags(tag_names_new)

        if not draft:
            draft = False
        else:
            draft = (draft.lower() == 'on')

        article = Article.get(id) if id else None
        new_article = False
        if article:
            # It's an edit of an existing item.
            just_published = article.draft and (not draft)
            # update the object
            article.title = title
            article.body = body
            article.tags = tag_objects_new
            article.draft = draft
        else:
            # It's new.
            article = Article(title=title,
                              body=body,
                              tags=tag_objects_new,
                              draft=draft)
            just_published = not draft
            new_article = True

        article.save()

        if new_article:
            Slug.insert_new(slug, article)

        if just_published:
            logging.debug('Article %d just went from draft to published. '
                          'Alerting the media.' % article.id)
            alert_the_media()

        TagCloud.reset()
        
        if url_from:
            self.redirect(url_from)
        else:
            self.redirect(utils.get_article_path(article))

class DeleteArticleHandler(request.BlogRequestHandler):
    # TODO: rewrite it to method GET
    def get(self):
        id = int(self.request.get('id'))
        article = Article.get(id)
        if article:
            article.delete()
            TagCloud.reset()

        #url_from = self.request.get("from")
        #if url_from:
        #    self.redirect(url_from)
        #else:
        #    self.redirect('/')
        self.redirect('/')

class DeleteCommentHandler(request.BlogRequestHandler):
    def get(self, comment_id):
        comment_id = int(comment_id)
        comment = Comment.get(comment_id)
        if comment:
            article = comment.article
            comment.delete()
            self.redirect(utils.get_article_path(article))
        else:
            self.redirect('/')

class Slugify(request.BlogRequestHandler):
    def get(self, text):
        text = urllib.unquote(text)
        #raise Exception(type(text))
        text = unicode(text, encoding='utf-8')
        self.response.out.write(utils.slugify(text))

class ListSlugs(request.BlogRequestHandler):
    def get(self):
        for slug in Slug.all():
            self.response.out.write('<li>%s -> %s' % (slug.slug, slug.article.id))

class ShowHeaders(request.BlogRequestHandler):
    def get(self):
        self.response.out.write('url: %s\n<br>' % self.request.url)
        self.response.out.write('path: %s\n<br>' % self.request.path)
        self.response.out.write('remote_addr: %s\n<br>' % self.request.remote_addr)
        self.response.out.write('\n<br>')
        for key in self.request.headers:
            self.response.out.write('%s: %s\n<br>' % (key, self.request.headers[key]))
        self.response.out.write('\n<br>%s' % self.request.body)

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------

# Right now, we only alert Technorati
#import technorati
#technorati.ping_technorati()
def alert_the_media():
    pass


application = webapp.WSGIApplication(
        [
         ('/admin/?', ShowAdminMainPageHandler),
         ('/admin/article/new/?', NewArticleHandler),
         ('/admin/article/delete/?', DeleteArticleHandler),
         ('/admin/article/save/?', SaveArticleHandler),
         ('/admin/article/edit/(\d+)$', EditArticleHandler),
         ('/admin/comment/delete/(\d+)$', DeleteCommentHandler),
         ('/admin/setup-basic-tags', SetupBasicTags),
         ('/admin/recalculate-tag-counters', RecalculateTagCountersFromArticles),
         ('/admin/reset-tag-counters', ResetTagCounters),
         ('/admin/empty-db', EmptyDB),
         ('/admin/tags', ManageTags),
         ('/admin/slugify/(.*)$', Slugify),
         ('/admin/slugs/?$', ListSlugs),
         ('/admin/headers', ShowHeaders),
         ],
        debug=True)

def main():
    util.run_wsgi_app(application)

if __name__ == "__main__":
    main()
