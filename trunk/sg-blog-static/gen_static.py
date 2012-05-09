import cgi
import codecs
import glob
import os
import datetime
import re

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
import sys

import clevermarkup
import defs
from userinfo import UserInfo
import utils
from operaimport.post_parser import parse_date_string
from operaimport.tag_rewrite import rewrite_tag

webapp.template.register_template_library('my_tags')

# info about tags used in articles, etc
class BlogMeta:
    INSTANCE = None

    @classmethod
    def instance(cls):
        if not cls.INSTANCE:
            cls.INSTANCE = cls._collect_metadata()
        return cls.INSTANCE

    @classmethod
    def _collect_metadata(cls):
        articles_by_tags = {}
        for md_short in glob.glob1(defs.MARKDOWN_DIR, '*'):
            md_full = os.path.join(defs.MARKDOWN_DIR, md_short)
            print >>sys.stderr, 'md:', md_full
            md = MarkdownFile.parse(md_full, read_content=False)
            #print >>sys.stderr, '  tags:', md.meta['tags']
            #print >>sys.stderr, '  date:', md.meta['date']

            for tag in md.meta['tags']:
                if articles_by_tags.has_key(tag):
                    articles_by_tags[tag].append(md)
                else:
                    articles_by_tags[tag] = [md]
        return articles_by_tags


class MarkdownFile():
    def __init__(self, meta, text):
        self.meta = meta
        self.text = text

    @classmethod
    def parse(cls, file, read_content = True):
        MD_PROPERTY_REGEX = re.compile('\s*#\s*'  '([a-zA-Z0-9_-]+)'  '\s*:\s*'  '(.*)'  '\s*')
        slug = os.path.split(file)[-1]
        #raise Exception('setting slug to: %s' % (slug,))
        meta = {
            'slug': slug
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
    articles_by_tags = BlogMeta.instance()

    md_file = os.path.join(defs.MARKDOWN_DIR, slug)

    print >>sys.stderr, 'Generating for %s ...' % md_file

    md = MarkdownFile.parse(md_file)
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
        'tag_cloud'       : articles_by_tags,
        'single_article'  : True,
        }
    html = render_template('articles.html', template_variables)
    html_file = os.path.join(defs.STATIC_HTML_DIR, '%s' % slug)
    utils.write_file(html_file, html)


def generate_tag_page(tag_name):
    articles_by_tags = BlogMeta.instance()

    # generate tag page(s)
    mds = articles_by_tags[tag_name]
    mds = sorted(mds, key=lambda md: md.meta['date'], reverse=True)
    #raise Exception('%s' % (len(mds),))
    template_variables = {
        'paging_title': 'There are %d articles tagged <b>%s</b>:' % (len(mds), tag_name),
        'articles':     mds,
        'tag_cloud':    articles_by_tags,
    }
    html = render_template('tag.html', template_variables)
    html_file = os.path.join(defs.STATIC_HTML_TAG_DIR, tag_name)
    utils.write_file(html_file, html)


def fetch_articles_sorted():
    mds = []
    for md_short in glob.glob1(defs.MARKDOWN_DIR, '*'):
        md_full = os.path.join(defs.MARKDOWN_DIR, md_short)
        md = MarkdownFile.parse(md_full, read_content=True)
        mds.append(md)
    mds = sorted(mds, key=lambda md: md.meta['date'], reverse=True)

    articles = []
    for md in mds:
        clever_object = clevermarkup.markup2html(md.text, for_comment=False)
        article = ArticleDataStoreMock(clever_object, md.meta)
        articles.append(article)

    return articles


def page_url(page1):
    return '/page%d' % page1 if page1 > 1 else '/'

def page_file(page1):
    return 'index.html' if page1 == 1 else 'page%d' % page1

def generate_listings():
    def generate_page(articles, html_file_short, current_page_1, pages_total):

        template_variables = {
            'articles': articles,
            'current_page_1': current_page_1,
            'pages_total': pages_total,
            'prev_page_url': page_url(current_page_1-1) if current_page_1 >= 2 else None,
            'next_page_url': page_url(current_page_1+1) if current_page_1 < pages_total else None,
            'single_article'  : False,
            'tag_cloud'       : BlogMeta.instance(),
            }
        html = render_template('articles.html', template_variables)
        html_file = os.path.join(defs.STATIC_HTML_DIR, html_file_short)
        utils.write_file(html_file, html)

    articles = fetch_articles_sorted()

    pages = utils.split_list_into_chunks(articles, defs.MAX_ARTICLES_PER_PAGE)
    for page0 in xrange(len(pages)):
        page1 = page0 + 1
        page = pages[page0]
        html_file_short = page_file(page1)
        generate_page(page, html_file_short, current_page_1=page1, pages_total=len(pages))


def generate_listing(page1):
    generate_listings()
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


def render_template(template_name, variables):
    tpl_path = os.path.join(os.path.dirname(__file__),
        defs.THEME_DIR,
        defs.TEMPLATE_DIR,
        template_name)
    return template.render(tpl_path, variables)


def generate_all():
    articles_by_tags = BlogMeta.instance()

    # generate every article
    for short_file in glob.glob1(defs.MARKDOWN_DIR, '*'):
        generate_article(short_file)

    generate_listings()

    # generate every tag
    for tag in articles_by_tags.keys():
        print >>sys.stderr, ' a tag "%s"' % tag
        generate_tag_page(tag)

    generate_rss()


if __name__ == '__main__':
    #generate_all()
    generate_article('jazz-78-lp1')
