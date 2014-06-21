# -*- coding: utf-8 -*-

# this must go first - this var is to be checked in defs.py
import os
import urllib

from operaimport import tags_categorized


os.environ.setdefault('SERVER_PROFILE', 'PRODUCTION')

import glob
import datetime
import sys
import jinja2
from jinja2 import Environment, FileSystemLoader

import defs
import clevermarkup
from comment_db import CommentDB
from userinfo import UserInfo
from MarkdownFile import MarkdownFile
import utils

#register = template.Library()
#register.filter('typographus', typographus.typo)

#class OnlyOnceExtension(Extension):
#    tags = set(['static_resource'])
#    @contextfunction
#    def parse(self, parser):
#        return Output("My Owl Extension")


class DictOfLists(dict):
    def __init__(self):
        super(DictOfLists, self).__init__()

    def append(self, key, value):
        if self.has_key(key):
            assert isinstance(self[key], list)
            self[key].append(value)
        else:
            self[key] = [value]


def page_url(page1):
    return '/page/%d.html' % page1 if page1 > 1 else '/'


def page_file(page1):
    return 'index.html' if page1 == 1 else 'page/%d.html' % page1


def static_resource_filter(value):
    hash_code = BlogMeta.instance().get_resource_hash(value)
    if hash_code:
        return '/static/%s?v=%s' % (value, hash_code)
    else:
        return '/static/%s' % value


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
    env = Environment(loader=FileSystemLoader(defs.THEME_DIRS), extensions=[])

    def typographus(value):
        from typographus import typo

        if isinstance(value, jinja2.runtime.Undefined):
            value = ''
        if type(value) == str:
            value = unicode(value)
        return typo(value)

    def blog_tag(value, tag_name, tag_title=None):
        if not tag_title:
            tag_title = tag_name
        return '<a href="/tag/%s.html">%s</a>' % (tag_name, tag_title)

    def blog_tag_cnt(value, tag_cloud, blog_tag_name, blog_tag_title=None):
        if not blog_tag_title:
            blog_tag_title = blog_tag_name
        mapp = tag_cloud.articles_by_tags
        count = len(mapp[blog_tag_name]) if mapp.has_key(blog_tag_name) else 0
        if count > 0:
            return '<a href="/tag/%s.html">%s</a> <span class="count">%s</span>' % (
                blog_tag_name, blog_tag_title, count)
        else:
            return '%s' % blog_tag_title

    def sidebar_link(value, title, description, url):
        #return '<li><a href="%s">%s</a><br>\n<span class="description">%s</span></li>\n' % (url, title, description.lower())
        return '<li><a href="%s" title="%s">%s</a>' % (url, description.lower(), title)

    def urlencode(value):
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        return urllib.quote(value, '')

    env.filters['urlencode'] = urlencode
    env.filters['sidebar_link'] = sidebar_link
    env.filters['static_resource'] = static_resource_filter
    env.filters['typographus'] = typographus
    env.filters['blog_tag'] = blog_tag
    env.filters['blog_tag_cnt'] = blog_tag_cnt
    tpl = env.get_template(template_name)
    return tpl.render(variables)


#webapp.template.register_template_library('my_tags')


class ResourceMeta:
    def __init__(self, path):
        self.path = path
        self.last_updated = None
        self.hash = None

    def get_hash(self):
        if not os.path.exists(self.path):
            print "path does not exist: %s" % self.path
            return None
        mtime = os.path.getmtime(self.path)
        # print "mtime old: %s" % self.last_updated
        # print "mtime new: %s" % mtime
        if self.last_updated is None or self.last_updated < mtime:
            self.hash = utils.file_md5_hex(self.path)
            # print "new hash calculated: %s %s" % (self.path, self.hash)
        self.last_updated = mtime
        # self.hash = utils.md5sum(self.path)
        return self.hash


# info about tags used in articles, etc
class BlogMeta:
    INSTANCE = None

    def __init__(self, articles_by_slugs, articles_by_tags):
        self.articles_by_slugs = articles_by_slugs
        self.articles_by_tags = articles_by_tags
        self.resource_by_path = dict()

    @classmethod
    def reset(cls):
        cls.INSTANCE = None

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

    def get_all_articles(self):
        return self.articles_by_slugs.values()

    @classmethod
    def instance(cls):
        if not cls.INSTANCE:
            cls.INSTANCE = cls._collect_metadata()
        return cls.INSTANCE

    @classmethod
    def _collect_metadata(cls):
        articles_by_slugs = {}
        articles_by_tags = DictOfLists()
        for md_short in glob.glob1(defs.MARKDOWN_DIR, '*'):
            md_full = os.path.join(defs.MARKDOWN_DIR, md_short)
            if os.path.isfile(md_full):
                print >> sys.stderr, 'md:', md_full

                md = MarkdownFile.parse(md_full, read_content=False)
                articles_by_slugs[md.meta['slug']] = md

                cls.fix_country_tag(md)

                if 'tags' in md.meta:
                    for tag in md.meta['tags']:
                        articles_by_tags.append(tag, md)

        res = BlogMeta(articles_by_slugs, articles_by_tags)
        return res

    # add tag 'russia' to article missing country tag
    @classmethod
    def fix_country_tag(cls, md):
        if 'tags' in md.meta:
            region_tags = tags_categorized.get_region_tags()
            intersection = set(md.meta['tags']) & set(region_tags)
            if not len(intersection):
                need_country = len(set(md.meta['tags']) & {'info', 'mix'}) == 0
                if need_country:
                    md.meta['tags'].append(defs.DEFAULT_COUNTRY_TAG)

    def get_resource_hash(self, path):
        full_path = os.path.join(defs.THEME_DIR, 'static', path)
        if not os.path.exists(full_path):
            print "path does not exist: %s" % full_path
            return None
        rm = self.resource_by_path.get(full_path)
        if rm is None:
            rm = ResourceMeta(full_path)
            self.resource_by_path[full_path] = rm
        return rm.get_hash()


def get_related_articles(article):
    ra = []
    blog_meta = BlogMeta.instance()
    the_tag = tags_categorized.get_tag_for_related_articles(article.tags)

    if article.see_list:
        ra = [blog_meta.articles_by_slugs[slug] for slug in article.see_list]
        ra = map(lambda md: article_from_markup(md), ra)
    elif the_tag:
        ra = blog_meta.articles_by_tags[the_tag]
        ra = [a for a in ra if a.meta['slug'] != article.slug]
        if len(ra) > 0:
            ra = sorted(ra, key=lambda x: x.meta.get('slug'))
            multi_article_hasher = lambda sum, a: "%s_%s" % (sum, utils.hexdigest(a.meta.get('slug')))
            multi_hash = reduce(multi_article_hasher, ra)
            ra = utils.pick_pseudo_random_elements(multi_hash, ra, 3)

    return ra


class ArticleDataStoreMock():
    def __init__(self, clever_object, meta):
        self.redirect = None

        if meta.has_key('redirect'):
            self.redirect = meta['redirect']
        else:
            assert type(meta['date']) == datetime.datetime
            assert type(meta['tags']) in (list, set)

            self.title = meta['title']
            self.complex_html = clever_object
            self.pinned = False
            self.published_date = meta['date']
            self.tags = meta['tags']
            self.slug = meta['slug']
            self.path = utils.get_article_path(self)
            self.url = utils.get_article_url(self)
            self.guid = utils.get_article_guid(self)
            #self.see_list = ['my-electro-proto-rap-mix-1982-92'] if meta.has_key('see') else None
            self.see_list = None

            self.related_articles = get_related_articles(self)

            self.title = self.title.replace(u'/', u'•')


def generate_article(slug):
    blog_meta = BlogMeta.instance()
    articles_by_tags = blog_meta.articles_by_tags

    md_file = os.path.join(defs.MARKDOWN_DIR, slug)

    print >> sys.stderr, 'Generating for %s ...' % md_file

    #md = MarkdownFile.parse(md_file)
    md = blog_meta.get_article_by_slug(slug)
    clever_object = clevermarkup.markup2html(md.text, for_comment=False)

    #print 'clever_object:', type(clever_object['middle'])

    #print >>sys.stderr, 'named at gen_static:', clever_object['named'].keys()
    #for p in clever_object['named']:
    #    print >>sys.stderr, '-', type(p)

    article = ArticleDataStoreMock(clever_object, md.meta)

    if article.redirect:
        target_title = blog_meta.articles_by_slugs[article.redirect].meta['title']
        template_variables = {
            'defs': defs,
            'tag_cloud': blog_meta,
            'redirect_url': '/%s.html' % article.redirect,
            'redirect_title': target_title,
        }
        html = render_template('redirect.html', template_variables)

    else:
        articles = [article]

        comments_db = CommentDB.get_instance('operaimport/comments4json.result.json')
        db_path = '/%s.html' % slug
        comments = comments_db.get_comments_for_path(db_path)
        #raise Exception('%s -> %s' % (db_path, comments,))

        #raise Exception('%s' % (article.complex_html['named']['info'],))

        template_variables = {
            'defs': defs,
            #'current_path'      : utils.get_article_path(slug),
            #'current_path_full' : utils.get_article_url(slug),
            'articles': articles,
            'user_info': UserInfo(),
            #'comment_author'  : utils.get_unicode_cookie(self.request, 'comment_author', ''),
            'comment_author': 'fake',
            'prev_page_url': None, #page_info.prev_page_url,
            'next_page_url': None, #page_info.next_page_url,
            'current_page_1': None, #page_info.current_page,
            'pages_total': None, #page_info.pages_total,
            'tag_cloud': blog_meta,
            'single_article': article,
            'comments': comments if comments else [],
        }
        html = render_template('articles.html', template_variables)

    html_file = os.path.join(defs.STATIC_HTML_DIR, '%s.html' % slug)
    utils.write_file(html_file, html)
    return html_file


def generate_tag(tag_name):
    html = generate_tag_page_content(tag_name)
    html_file = os.path.join(defs.STATIC_HTML_TAG_DIR, '%s.html' % tag_name)
    utils.write_file(html_file, html)
    return html_file


def generate_tag_page_content(tag_name):
    blog_meta = BlogMeta.instance()
    articles_by_tags = blog_meta.articles_by_tags

    # generate tag page(s)
    mds = articles_by_tags[tag_name]
    mds = sorted(mds, key=lambda md: md.meta['date'], reverse=True)
    articles = [article_from_markup(md) for md in mds]
    #raise Exception('%s' % (len(mds),))

    about_text = tags_categorized.get_about_text(tag_name)

    template_variables = {
        'tag_title': tag_name,
        'about_text': about_text,
        'articles_count': len(mds),
        'paging_title': 'There are %d articles tagged <b>%s</b>:' % (len(mds), tag_name),
        'articles': articles,
        'tag_cloud': blog_meta,
        'defs': defs,
    }
    return render_template('tag.html', template_variables)


def generate_tag_cat():
    html_file = os.path.join(defs.STATIC_HTML_TAG_DIR, 'all.html')
    cats, uncat = tags_categorized.get_used_tags_categories()
    #raise Exception('len(uncat): %s' % (len(uncat),))
    tpl_vars = {
        'defs': defs,
        'tag_cloud': BlogMeta.instance(),
        'categories': cats,
        'uncategorized': uncat,
    }
    html = render_template('tag-listing.html', tpl_vars)
    utils.write_file(html_file, html)
    return html_file


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
    mds = filter(lambda md: not md.meta.has_key('redirect'), mds)
    mds = sorted(mds, key=lambda md: md.meta['date'], reverse=True)

    articles = []
    for md in mds:
        #clever_object = clevermarkup.markup2html(md.text, for_comment=False)
        #article = ArticleDataStoreMock(clever_object, md.meta)
        #articles.append(article)
        articles.append(article_from_markup(md))

    return articles


# param one_page1_required allows us optimize HTML generation by just one page
def generate_listings(one_page1_required=None):
    def generate_page(articles, current_page_1, pages_total):
        html_file_short = page_file(current_page_1)
        template_variables = {
            'articles': articles,
            'current_page_1': current_page_1,
            'pages_total': pages_total,
            'prev_page_url': page_url(current_page_1 - 1) if current_page_1 >= 2 else None,
            'next_page_url': page_url(current_page_1 + 1) if current_page_1 < pages_total else None,
            'single_article': False,
            'tag_cloud': BlogMeta.instance(),
            'defs': defs,
            'a_listing_page': True, # a marker for pages '/' and '/page/15.html'
        }
        html = render_template('articles.html', template_variables)
        html_file = os.path.join(defs.STATIC_HTML_DIR, html_file_short)
        utils.write_file(html_file, html)

    if one_page1_required >= 1:
        # generate just one HTML file
        blog_meta = BlogMeta.instance()
        mds = blog_meta.get_all_articles()
        mds = filter(lambda md: not md.meta.has_key('redirect'), mds)
        mds = sorted(mds, key=lambda md: md.meta['date'], reverse=True)
        start = (one_page1_required - 1) * defs.MAX_ARTICLES_PER_PAGE
        mds = mds[start:  start + defs.MAX_ARTICLES_PER_PAGE]
        page = [article_from_markup(md) for md in mds]
        pages_total = len(blog_meta.articles_by_slugs.values())
        generate_page(page, one_page1_required, pages_total)
    else:
        # generate every listing page
        articles = fetch_articles_sorted()
        pages = utils.split_list_into_chunks(articles, defs.MAX_ARTICLES_PER_PAGE)

        for page0 in xrange(len(pages)):
            page1 = page0 + 1
            page = pages[page0]
            generate_page(page, current_page_1=page1, pages_total=len(pages))


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


def generate_search():
    html_file = os.path.join(defs.STATIC_HTML_DIR, 'special', 'search.html')
    template_variables = {
        'defs': defs,
        'tag_cloud': BlogMeta.instance(),
    }
    html = render_template('search.html', template_variables)
    utils.write_file(html_file, html)
    return html_file


def generate_all():
    print 'collecting meta...'
    blog_meta = BlogMeta.instance()
    articles_by_tags = blog_meta.articles_by_tags

    # generate every article
    print 'generating articles...'
    for short_file in glob.glob1(defs.MARKDOWN_DIR, '*'):
        if os.path.isfile(os.path.join(defs.MARKDOWN_DIR, short_file)):
            generate_article(short_file)

    # generate every tag
    print 'generating tags...'
    for tag in articles_by_tags.keys():
        print >> sys.stderr, ' a tag "%s"' % tag
        generate_tag(tag)

    # tag categories (site map)
    generate_tag_cat()

    print 'generating front page and others...'
    generate_listings()

    print 'generating rss.xml...'
    generate_rss()

    print 'generating search page...'
    generate_search()


if __name__ == '__main__':
    print 'start'
    generate_all()
    #generate_article('jaan-kuman-tantsurutme-complete')
    #generate_rss()