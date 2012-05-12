import cgi
import codecs
import glob
import os
import datetime
import re
import sys
import jinja2
from jinja2.ext import Extension
from jinja2.nodes import Output
from jinja2.utils import contextfunction

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_generator.settings")

#from google.appengine.ext import webapp
#from google.appengine.ext.webapp import template
from django.shortcuts import render_to_response
from django import template
from django.template import loader
from django.template.context import Context
from jinja2 import Environment, FileSystemLoader

import clevermarkup
import defs
from userinfo import UserInfo
import utils
from operaimport.post_parser import parse_date_string
from operaimport.tag_rewrite import rewrite_tag
import typographus

register = template.Library()
register.filter('typographus', typographus.typo)

#class OnlyOnceExtension(Extension):
#    tags = set(['static_resource'])
#    @contextfunction
#    def parse(self, parser):
#        return Output("My Owl Extension")

def render_template(template_name, variables):
    # GAE
    #tpl_path = os.path.join(os.path.dirname(__file__),
    #    defs.THEME_DIR,
    #    defs.TEMPLATE_DIR,
    #    template_name)
    #return template.render(tpl_path, variables)

    # Django
    #tpl = loader.get_template(template_name)
    #c = Context(variables)
    #return tpl.render(c)

    # Jinja2
    env = Environment(loader=FileSystemLoader('themes/grid'), extensions=[])
    def static_resource(value):
        return '/static/%s' % value
    def typographus(value):
        from typographus import typo
        if isinstance(value, jinja2.runtime.Undefined):
            value = ''
        if type(value) == str:
            value = unicode(value)
        return typo(value)
    def blog_tag(value, tag_name, tag_title = None):
        if not tag_title:
            tag_title = tag_name
        return '<a href="/tag/%s">%s</a>' % (tag_name, tag_title)
    def blog_tag_cnt(value, tag_cloud, blog_tag_name, blog_tag_title = None):
        if not blog_tag_title:
            blog_tag_title = blog_tag_name
        mapp = tag_cloud.articles_by_tags
        count = len(mapp[blog_tag_name]) if mapp.has_key(blog_tag_name) else 0
        if count > 0:
            return '<a href="/tag/%s">%s</a> <span>%s</span>' % (blog_tag_name, blog_tag_title, count)
        else:
            return '%s' % blog_tag_title

    env.filters['static_resource'] = static_resource
    env.filters['typographus'] = typographus
    env.filters['blog_tag'] = blog_tag
    env.filters['blog_tag_cnt'] = blog_tag_cnt
    tpl = env.get_template(template_name)
    return tpl.render(variables)


#webapp.template.register_template_library('my_tags')

# info about tags used in articles, etc
class BlogMeta:
    INSTANCE = None

    def __init__(self, articles_by_slugs, articles_by_tags):
        self.articles_by_slugs = articles_by_slugs
        self.articles_by_tags = articles_by_tags

    def get_article_by_slug(self, slug):
        md = self.articles_by_slugs[slug]
        md_file = os.path.join(defs.MARKDOWN_DIR, slug)
        t1 = md.meta['mtime']
        t2 = os.path.getmtime(md_file)
        if t1 < t2:
            md = MarkdownFile.parse(md_file)
            self.articles_by_slugs[md.meta['slug']] = md
            #raise Exception('%s' % ('changed!',))
        return md

    @classmethod
    def instance(cls):
        if not cls.INSTANCE:
            cls.INSTANCE = cls._collect_metadata()
        return cls.INSTANCE

    @classmethod
    def _collect_metadata(cls):
        articles_by_slugs = {}
        articles_by_tags = {}
        for md_short in glob.glob1(defs.MARKDOWN_DIR, '*'):
            md_full = os.path.join(defs.MARKDOWN_DIR, md_short)
            if os.path.isdir(md_full):
                continue
            print >>sys.stderr, 'md:', md_full
            md = MarkdownFile.parse(md_full, read_content=False)
            articles_by_slugs[md.meta['slug']] = md
            #print >>sys.stderr, '  tags:', md.meta['tags']
            #print >>sys.stderr, '  date:', md.meta['date']

            for tag in md.meta['tags']:
                if articles_by_tags.has_key(tag):
                    articles_by_tags[tag].append(md)
                else:
                    articles_by_tags[tag] = [md]
        return BlogMeta(articles_by_slugs, articles_by_tags)


class MarkdownFile():
    def __init__(self, meta, text):
        self.meta = meta
        self.text = text

    @classmethod
    def parse(cls, file, read_content = True):

        read_content = True # todo: the param rewritten!

        MD_PROPERTY_REGEX = re.compile('\s*#\s*'  '([a-zA-Z0-9_-]+)'  '\s*:\s*'  '(.*)'  '\s*')
        slug = os.path.split(file)[-1]
        #raise Exception('setting slug to: %s' % (slug,))
        meta = {
            'slug': slug,
            'mtime': os.path.getmtime(file),
        }
        f = codecs.open(file, "r", defs.HTML_ENCODING)
        try:
            while True:
                line = f.readline().strip()
                m = re.match(MD_PROPERTY_REGEX, line)
                if m:
                    key = m.group(1).lower()
                    value = m.group(2)
                    if key == 'tags':
                        value = cls._handle_tags(value)
                    elif key == 'date':
                        value = parse_date_string(value)
                    meta[key] = value
                elif line == '':
                    break
                else:
                    raise Exception('markup file format error for %s -> "%s"' % (file, line))
            text = f.read(6000000).strip() if read_content else None # todo: what the fuck with that read?!
            return MarkdownFile(meta, text)
        finally:
            f.close()

    @classmethod
    def _handle_tags(cls, string_value):
        tags = utils.split_and_strip_tags(string_value.lower(), ',')
        tags = map(rewrite_tag, tags)
        return tags


class ArticleDataStoreMock():
    def __init__(self, clever_object, meta):
        assert type(meta['date']) == datetime.datetime
        assert type(meta['tags']) in (list, set)

        #raise Exception('%s' % (clever_object['named'],))

        self.title = meta['title']
        self.complex_html = clever_object
        self.pinned = False
        self.published_date = meta['date']
        self.tags = meta['tags']
        self.slug = meta['slug']
        self.url = utils.get_article_url(self)
        self.guid = utils.get_article_guid(self)

def generate_article(slug):
    blog_meta = BlogMeta.instance()
    articles_by_tags = blog_meta.articles_by_tags

    md_file = os.path.join(defs.MARKDOWN_DIR, slug)

    print >>sys.stderr, 'Generating for %s ...' % md_file

    #md = MarkdownFile.parse(md_file)
    md = blog_meta.get_article_by_slug(slug)
    clever_object = clevermarkup.markup2html(md.text, for_comment=False)

    #print 'clever_object:', type(clever_object['middle'])

    #print >>sys.stderr, 'named at gen_static:', clever_object['named'].keys()
    #for p in clever_object['named']:
    #    print >>sys.stderr, '-', type(p)

    article = ArticleDataStoreMock(clever_object, md.meta)
    articles = [ article ]

    #raise Exception('%s' % (article.complex_html['named']['info'],))

    template_variables = {
        'defs'         : defs,
        'current_path' : 'fake-current-path',
        'articles'     : articles,
        'user_info'    : UserInfo(),
        #'comment_author'  : utils.get_unicode_cookie(self.request, 'comment_author', ''),
        'comment_author'  : 'fake',
        'prev_page_url'   : None, #page_info.prev_page_url,
        'next_page_url'   : None, #page_info.next_page_url,
        'current_page_1'  : None, #page_info.current_page,
        'pages_total'     : None, #page_info.pages_total,
        'tag_cloud'       : blog_meta,
        'single_article'  : article,
        }
    html = render_template('articles.html', template_variables)
    html_file = os.path.join(defs.STATIC_HTML_DIR, '%s' % slug)
    utils.write_file(html_file, html)
    return html_file


def generate_tag_page(tag_name):
    blog_meta = BlogMeta.instance()
    articles_by_tags = blog_meta.articles_by_tags

    # generate tag page(s)
    mds = articles_by_tags[tag_name]
    mds = sorted(mds, key=lambda md: md.meta['date'], reverse=True)
    #raise Exception('%s' % (len(mds),))
    template_variables = {
        'paging_title': 'There are %d articles tagged <b>%s</b>:' % (len(mds), tag_name),
        'articles':     mds,
        'tag_cloud':    blog_meta,
        'defs':         defs,
    }
    html = render_template('tag.html', template_variables)
    html_file = os.path.join(defs.STATIC_HTML_TAG_DIR, tag_name)
    utils.write_file(html_file, html)

def article_from_markup(md):
    assert isinstance(md, MarkdownFile)
    clever_object = clevermarkup.markup2html(md.text, for_comment=False)
    return ArticleDataStoreMock(clever_object, md.meta)

def fetch_articles_sorted():
    mds = []
    for md_short in glob.glob1(defs.MARKDOWN_DIR, '*'):
        md_full = os.path.join(defs.MARKDOWN_DIR, md_short)
        if os.path.isfile(md_full):
            md = MarkdownFile.parse(md_full, read_content=True)
            mds.append(md)
    mds = sorted(mds, key=lambda md: md.meta['date'], reverse=True)

    articles = []
    for md in mds:
        #clever_object = clevermarkup.markup2html(md.text, for_comment=False)
        #article = ArticleDataStoreMock(clever_object, md.meta)
        #articles.append(article)
        articles.append(article_from_markup(md))

    return articles


def page_url(page1):
    return '/page/%d' % page1 if page1 > 1 else '/'

def page_file(page1):
    return 'index.html' if page1 == 1 else 'page/%d' % page1

def generate_listings(one_page1_required = None):
    def generate_page(articles, html_file_short, current_page_1, pages_total):
        template_variables = {
            'articles'       : articles,
            'current_page_1' : current_page_1,
            'pages_total'    : pages_total,
            'prev_page_url'  : page_url(current_page_1-1) if current_page_1 >= 2 else None,
            'next_page_url'  : page_url(current_page_1+1) if current_page_1 < pages_total else None,
            'single_article' : False,
            'tag_cloud'      : BlogMeta.instance(),
            'defs'           : defs,
            }
        html = render_template('articles.html', template_variables)
        html_file = os.path.join(defs.STATIC_HTML_DIR, html_file_short)
        utils.write_file(html_file, html)

#    if one_page1_required >= 1:
#        blog_meta = BlogMeta.instance()
#        mds = sorted(blog_meta.all_articles, key=lambda md: md.meta['date'], reverse=True)
#        start = (one_page1_required - 1) * defs.MAX_ARTICLES_PER_PAGE
#        mds = mds[ start :  start + defs.MAX_ARTICLES_PER_PAGE ]
#        articles = [ article_from_markup(md) for md in mds]
#        pages = [ articles ]
#    else:
    articles = fetch_articles_sorted()
    pages = utils.split_list_into_chunks(articles, defs.MAX_ARTICLES_PER_PAGE)

    for page0 in xrange(len(pages)):
        page1 = page0 + 1
        page = pages[page0]
        html_file_short = page_file(page1)
        generate_page(page, html_file_short, current_page_1=page1, pages_total=len(pages))


def generate_listing(page1):
    generate_listings(page1)
    html_file_short = page_file(page1)
    return os.path.join(defs.STATIC_HTML_DIR, html_file_short)


def generate_rss():
    html_file = os.path.join(defs.STATIC_HTML_DIR, 'special', 'rss.xml')
    articles = utils.limit(fetch_articles_sorted(), defs.MAX_ARTICLES_RSS)
    last_updated = articles[0].published_date
    template_variables = {
        'articles': articles,
        'defs': defs,
        'last_updated': last_updated,
    }
    html = render_template('rss-articles.xml', template_variables)
    utils.write_file(html_file, html)
    return html_file


def generate_all():
    blog_meta = BlogMeta.instance()
    articles_by_tags = blog_meta.articles_by_tags

    # generate every article
    for short_file in glob.glob1(defs.MARKDOWN_DIR, '*'):
        if os.path.isfile(os.path.join(defs.MARKDOWN_DIR, short_file)):
            generate_article(short_file)

    generate_listings()

    # generate every tag
    for tag in articles_by_tags.keys():
        print >>sys.stderr, ' a tag "%s"' % tag
        generate_tag_page(tag)

    generate_rss()


if __name__ == '__main__':
    generate_all()
    #generate_article('band-called-75-1979')
    #generate_rss()