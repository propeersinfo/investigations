import os
import cgi
import logging

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

from models import *
from utils import slugify
import request

from operablogimport.post_parser import parse_file

IMPORT_LIMIT = None

def import_post_object(post):
    def string2category(tag_name):
        tag_name = str(tag_name)
        #return db.Category(tag_name)
        assert type(tag_name) == str, "%s" % type(tag_name)
        return ArticleTag.get_by_name(tag_name, create_on_demand=True).key()

    def transaction():
        slug = post['slug']
#        Slug.assert_slug_unused(slug_string=slug)
        article = Article(title = post['title'],
                          slug = slug,
                          body = post['content'],
                          published_date = post['date'],
                          draft = False,
                          tags = map(string2category, post['tags']))
        article.save()
#        Slug.insert_new(slug, article)
        for comment in post['comments']:
            db_comment = Comment(article = article,
                                 author = comment['username'],
                                 blog_owner = comment['owner_comment'],
                                 text = comment['text'],
                                 published_date = comment['date'])
            db_comment.save()
        return article

    return transaction()

def import_file(fname):
    post = parse_file(fname)
    return import_post_object(post)

def import_all_files():
    import glob
    posts = []
    cnt = 0
    for file in glob.glob("../operabloghtml/*"):
        if IMPORT_LIMIT and cnt >= IMPORT_LIMIT:
            break
        if os.path.isfile(file):
            posts.append(parse_file(file))
            cnt += 1
    posts = sorted(posts, key=lambda post: post['date'])
    for post in posts:
        try:
            #out.write("%s %s\n" % (post['date'], post['title']))
            import_post_object(post)
        except db.BadValueError:
            raise Exception('BadValueError for file %s' % (file))

class ImportSomeHandler(request.BlogRequestHandler):
    def get(self):
        import_all_files()
        #one_file("operabloghtml\\via-75-ep", out)
        self.redirect('/admin/')

application = webapp.WSGIApplication(
        [('/admin/importdata/?', ImportSomeHandler)],
        debug=True)

def main():
    util.run_wsgi_app(application)

if __name__ == "__main__":
    main()
