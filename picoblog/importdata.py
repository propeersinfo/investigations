import cgi
import logging

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

from models import *
import request

from operablogimport.post_parser import parse_file

IMPORT_LIMIT = None

def import_post_object(post):
    def string2category(tag_name):
        tag_name = str(tag_name)
        #return db.Category(tag_name)
        assert type(tag_name) == str, "%s" % type(tag_name)
        return ArticleTag.get_by_name(tag_name, create_on_demand=True).key()

    article = Article(title = post['title'],
                      body = post['content'],
                      published_date = post['date'],
                      draft = False,
                      tags = map(string2category, post['tags']))
    article.save()

    for comment in post['comments']:
        db_comment = Comment(article = article,
                             author = comment['username'],
                             blog_owner = comment['owner_comment'],
                             text = comment['text'],
                             published_date = comment['date'])
        db_comment.save()

def import_file(fname, out):
    post = parse_file(fname)
    import_object(post)

def import_all_files(out):
    import glob
    posts = []
    cnt = 0
    for file in glob.glob("operabloghtml/*"):
        if IMPORT_LIMIT and cnt >= IMPORT_LIMIT:
            break
        posts.append(parse_file(file))
        cnt += 1
    posts = sorted(posts, key=lambda post: post['date'])
    for post in posts:
        #out.write("%s %s\n" % (post['date'], post['title']))
        import_post_object(post)

class ImportSomeHandler(request.BlogRequestHandler):
    def get(self):
        #articles = Article.get_all()
        out = self.response.out
        #out.write("<xmp>\n")
        #out.write("importing some\n")
        import_all_files(out)
        #one_file("operabloghtml\\via-75-ep", out)
        self.redirect('/admin/')

application = webapp.WSGIApplication(
        [('/importdata/?', ImportSomeHandler)],
        debug=True)

def main():
    util.run_wsgi_app(application)

if __name__ == "__main__":
    main()
