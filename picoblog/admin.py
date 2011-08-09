# $Id: f06befd2bc4b552d08c2d93836b674baa0dc417e $

"""
Google App Engine Script that handles administration screens for the
blog.
"""

import cgi
import logging

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from models import *
import request

import utils
from userinfo import UserInfo

from google.appengine.ext.webapp import template
template.register_template_library('my_tags')

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------

class ShowArticlesHandler(request.BlogRequestHandler):
    """
    Handles the main admin page, which lists all articles in the blog,
    with links to their corresponding edit pages.
    """
    def get(self):
        #articles = Article.get_all()
        #template_vars = {'articles' : articles}
        template_vars = {}
        self.response.out.write(self.render_template('admin-main.html',
                                                     template_vars))

class NewArticleHandler(request.BlogRequestHandler):
    """
    Handles requests to create and edit a new article.
    """
    def get(self):
        article = Article(title='-',
                          body=utils.read_file('new-article.txt'),
                          draft=False)
        user_info = UserInfo(self.request)
        template_vars = {
            'article'   : article,
            'user_info' : user_info
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
        body = self.request.get('content')
        s_id = cgi.escape(self.request.get('id'))
        id = int(s_id) if s_id else None
        tags = cgi.escape(self.request.get('tags'))
        published_date = cgi.escape(self.request.get('published_date'))
        draft = cgi.escape(self.request.get('draft'))
        if tags:
            tags = [t.strip() for t in tags.split(',')]
        else:
            tags = []
        tags = Article.convert_string_tags(tags)

        if not draft:
            draft = False
        else:
            draft = (draft.lower() == 'on')

        article = Article.get(id) if id else None
        if article:
            # It's an edit of an existing item.
            just_published = article.draft and (not draft)
            article.title = title
            article.body = body
            article.tags = tags
            article.draft = draft
        else:
            # It's new.
            article = Article(title=title,
                              body=body,
                              tags=tags,
                              draft=draft)
            just_published = not draft

        article.save()

        if just_published:
            logging.debug('Article %d just went from draft to published. '
                          'Alerting the media.' % article.id)
            alert_the_media()

        edit_again = cgi.escape(self.request.get('edit_again'))
        edit_again = edit_again and (edit_again.lower() == 'true')
        if edit_again:
            self.redirect('/admin/article/edit/?id=%s' % article.id)
        elif url_from:
            self.redirect(url_from)
        else:
            self.redirect(utils.get_article_path(article))

class EditArticleHandler(request.BlogRequestHandler):
    """
    Handles requests to edit an article.
    """
    def get(self, id):
        id = int(id)
        article = Article.get(id)
        if not article:
            raise ValueError, 'Article with ID %d does not exist.' % id

        article.tag_string = ', '.join(article.tags)
        template_vars = {
            'article'  : article,
            'from'     : cgi.escape(self.request.get('from'))
        }
        self.response.out.write(self.render_template('admin-edit.html',
                                                     template_vars))

class DeleteArticleHandler(request.BlogRequestHandler):
    # TODO: rewrite it to method GET
    def get(self):
        id = int(self.request.get('id'))
        article = Article.get(id)
        if article:
            article.delete()

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
         ('/admin/?', ShowArticlesHandler),
         ('/admin/article/new/?', NewArticleHandler),
         ('/admin/article/delete/?', DeleteArticleHandler),
         ('/admin/article/save/?', SaveArticleHandler),
         ('/admin/article/edit/(\d+)$', EditArticleHandler),
         ('/admin/comment/delete/(\d+)$', DeleteCommentHandler),
         ],

        debug=True)

def main():
    util.run_wsgi_app(application)

if __name__ == "__main__":
    main()
