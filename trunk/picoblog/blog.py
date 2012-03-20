import re
import urllib
import cgi

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import users

import caching
from models import *
import defs
import request
import utils
import clevermarkup as markup
from paging import PagedQuery, PageInfoBase, PageInfo, EmptyPageInfo, SinglePageInfo, NoPagingPageInfo
from userinfo import UserInfo

class AbstractPageHandler(request.BlogRequestHandler):
    def augment_articles(self, articles, url_prefix, produce_html=True):
        for article in articles:
            if article:
                if produce_html:
                    article.html = 'article.html is not available anymore'
                    article.complex_html = markup.markup2html(article.body, for_comment=False, article_id=article.id)
                article.path = utils.get_article_path(article)
                article.tag_objects = article.get_tag_objects()
                article.url = url_prefix + article.path
                article.guid = url_prefix + utils.get_article_guid(article)
                article.comments_count = article.comment_set.count()
                article.published_class = 'draft' if article.draft else 'published'
                #article.title = cgi.escape(article.title)
                if len(articles) == 1: # only for a concrete blog post page
                    self.augment_comments_for(article)
                article.pinned = article.published_date > datetime.datetime.now()

    def augment_comments_for(self, article):
        comments = []
        for comment in article.fetch_comments():
            comment.html = markup.markup2html(markup_text=comment.text,
                                              for_comment=True,
                                              rich_markup=False,
                                              recognize_links=comment.blog_owner)
            comment.repliable = (comment.id == comment.replied_comment_id)
            comments.append(comment)
        article.comments = comments

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

        user_info = UserInfo(request)

        template_variables = {
            'defs'         : defs,
            'current_path' : cgi.escape(request.path),
            'articles'     : articles,
            'user_info'    : user_info,
            'comment_author'  : utils.get_unicode_cookie(self.request, 'comment_author', ''),
            'prev_page_url'   : page_info.prev_page_url,
            'next_page_url'   : page_info.next_page_url,
            'current_page_1'  : page_info.current_page,
            'pages_total'     : page_info.pages_total,
            'tag_cloud'       : caching.TagCloud.get(),
            'desired_lang'    : self.extract_preferred_content_language(),
        }

        if additional_template_variables:
            template_variables.update(additional_template_variables)

        return self.render_template(template_name, template_variables)

    def extract_preferred_content_language(self):
        try:
            lang = self.request.headers['Accept-Language']
            return 'ru' if re.search('(,ru|ru;)', lang, re.IGNORECASE) else 'en'
        except KeyError:
            return 'en'

    def get_recent(self):
        return []

    def do_alternate_response_code(self, http_response_code):
        self.response.set_status(http_response_code)
        template = '%d.html' % http_response_code
        self.response.out.write(self.render_articles(EmptyPageInfo(), self.request, [], template))

class FrontPageHandler(AbstractPageHandler):
    @caching.show_page_load_time
    def get(self, *args, **kwargs):
        self.response.out.write(self.produce_html(*args, **kwargs))

    @caching.cacheable
    def produce_html(self, page_num = 1):
        page_num = int(page_num)
        q = Article.query_all() if users.is_current_user_admin() else Article.query_published()
        page_info = PageInfo(PagedQuery(q, defs.MAX_ARTICLES_PER_PAGE), page_num, "/page%d", "/")
        return self.render_articles(page_info, self.request, self.get_recent())

class AllTagsTagHandler(AbstractPageHandler):
    @classmethod
    def augment_tag_objects_for_weights(cls, tags):
        # augment tag objects with info about their popularity weights
        counts_and_weights = [
            { 'count': 4, 'weight': 3 },
            { 'count': 2, 'weight': 2 },
            { 'count': 0, 'weight': 1 },
        ]
        for tag in tags:
            cnt = tag.counter
            for cnw in counts_and_weights:
                if cnt >= cnw['count']:
                    tag.weight = cnw['weight']
                    break

    @caching.cacheable
    def render_html(self):
        tag_cloud = caching.TagCloud.get()

        # todo: try to avoid this augmentation each time
        self.__class__.augment_tag_objects_for_weights(tag_cloud.all_tags)

        tpl_vars = {
            'tag_cloud' : tag_cloud,
            'user_info' : UserInfo(self.request),
            }
        return self.render_template('tag-listing.html', tpl_vars)

    @caching.show_page_load_time
    def get(self):
        self.response.out.write(self.render_html())
	
class ArticlesByTagHandler(AbstractPageHandler):
    @caching.show_page_load_time
    def get(self, *args, **kwargs):
        self.response.out.write(self.produce_html(*args, **kwargs))

    @caching.cacheable
    def produce_html(self, tag_name, page_num = 1):
        page_num = int(page_num)
        tag_name = urllib.unquote(tag_name) # replace %20 with actual characters

        q = Article.query_for_tag_name(tag_name)
        paged_query = PagedQuery(q, defs.MAX_ARTICLES_PER_PAGE)
        page_info = PageInfo(paged_query,
                             page_num,
                             '/tag/%s/page%%d' % tag_name,
                             '/tag/%s/' % tag_name)
        tpl_vars = {
            'paging_title' : 'There are %s articles tagged &ldquo;%s&rdquo;.' % (paged_query.count(), tag_name)
        }
        return self.render_articles(page_info, self.request, self.get_recent(),
                                    additional_template_variables=tpl_vars)


class ArticleByIdHandler(AbstractPageHandler):
    def get(self, id):
        article = Article.get(int(id))
        if article:
            self.redirect(utils.get_article_path(article), permanent=True)
        else:
            self.do_alternate_response_code()

class ArticleBySlugHandler(ArticleByIdHandler):
    @caching.show_page_load_time
    def get(self, slug):
        slug_obj = Slug.find_article_by_slug(slug_string = slug)
        if slug_obj:
            article = slug_obj.article
            if article.draft and not users.is_current_user_admin():
                self.do_alternate_response_code(403)
            else:
                # don't set response code here - it gonna be set in cacheable() decorator
                self.response.out.write(self.produce_html(article))
        else:
            self.do_alternate_response_code(404)

    @caching.cacheable
    def produce_html(self, article):
        additional_template_variables = {'single_article': article}
        return self.render_articles(SinglePageInfo(article), self.request, self.get_recent(), 'articles.html',
            additional_template_variables)

class ArchivePageHandler(AbstractPageHandler):
    """
    Handles requests to display the list of all articles in the blog.
    """
    @caching.show_page_load_time
    def get(self, *args, **kwargs):
        self.response.out.write(self.produce_html(*args, **kwargs))

    @caching.cacheable
    def produce_html(self, page_num = 1):
        page_num = int(page_num) if page_num else 1
        q = Article.query_all() if users.is_current_user_admin() else Article.query_published()
        page_info = PageInfo(PagedQuery(q, defs.MAX_ARTICLES_PER_PAGE_ARCHIVE),
                             page_num,
                             "/archive/%d",
                             "/archive/")
        return self.render_articles(page_info, self.request, [], 'archive.html')


class RssArticlesHandler(AbstractPageHandler):
    """
    Handles request for an RSS2 feed of the blog's contents.
    """
    def get(self):
        pager = NoPagingPageInfo(PagedQuery(Article.query_published(), defs.MAX_ARTICLES_RSS))
        ct = 'text/plain' if self.request.get('format') == 'plain' else 'text/xml'
        self.response.headers['Content-Type'] = ct
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
        text = cgi.escape(self.request.get('text')).strip()

        comment = Comment(article = article,
                          author = author,
                          text = text,
                          blog_owner = users.is_current_user_admin(),
                          replied_comment_id = self.get_replied_comment_id())
        comment.save()
        utils.set_unicode_cookie(self.response, "comment_author", author)
        if defs.PRODUCTION:
            # e-mail sending is not set up on the dev server yet
            utils.send_mail_to_admin_about_new_comment(comment)
        self.redirect(utils.get_article_path(article))

webapp.template.register_template_library('my_tags')

application = webapp.WSGIApplication(
    [('/', FrontPageHandler),
     ('/page(\d+)/?', FrontPageHandler),
     ('/tag/?$', AllTagsTagHandler),
     ('/tag/([^/]+)/?$', ArticlesByTagHandler),
     ('/tag/([^/]+)/page(\d+)/?$', ArticlesByTagHandler),
     ('/archive/(\d+)?$', ArchivePageHandler),
     ('/rss/?$', RssArticlesHandler),
     ('/comment/add/(\d+)$', AddCommentHandler),
     ('/article/(\d+)$', ArticleByIdHandler),
     ('/(.*)$', ArticleBySlugHandler),
     ],
    debug=True)

def main():
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
