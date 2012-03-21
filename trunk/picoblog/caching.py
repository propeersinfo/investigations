# everything about caching is placed here


import datetime
import hashlib
import logging

from google.appengine.ext import db
from google.appengine.api import memcache, users

import defs
import models
import utils

HTTP_304_NOT_MODIFIED = 304

########################################################

class TagCloud():
    """
    All tags in memory, 2-3 KB
    """
    MEMCACHE_KEY = __name__

    def __init__(self):
        self.tag_count = {}
        self.categorized = {}

    def get_tag_usage_count(self, tag_name):
        return self.tag_count.get(tag_name, 0)

    @classmethod
    def get(cls):
        #raise Exception('%s' % cls.MEMCACHE_KEY)
        value = memcache.get(cls.MEMCACHE_KEY)
        if not value:
            value = cls.__make_cloud()
            # todo: keep it forever but don't forget to reset (patch) memcache when a tag changed in datastore
            #memcache.set(cls.MEMCACHE_KEY, value, utils.hours(24).seconds())
            memcache.set(cls.MEMCACHE_KEY, value, 5) # todo: not for production!
        return value

    @classmethod
    def reset(cls):
        memcache.delete(cls.MEMCACHE_KEY)

    @classmethod
    def __make_cloud(cls):
        cloud = TagCloud()
        cloud.all_tags = []
        for tag in models.ArticleTag.fetch_all():
            cloud.all_tags.append(tag)
            cloud.tag_count[tag.name] = tag.counter
            if cloud.categorized.has_key(tag.category):
                cloud.categorized[tag.category].append(tag)
            else:
                cloud.categorized[tag.category] = [ tag ]
        for cat in cloud.categorized:
            cloud.categorized[cat] = sorted(cloud.categorized[cat], key=lambda tag: tag.name)
        return cloud

# decorator
# HTML generation time will be printed in the bottom
# Apply it to RequestHandler.get() methods
def show_page_load_time(fun):
    def decorator(self, *args, **kwargs):
        plt = utils.PageLoadTime()
        fun(self, *args, **kwargs)
        plt.print_time(self.response.out)
    return decorator

# decorator
# HTML cache will be asked before to generate content
# ETag and 304 are implemented here
# HTTP response code is set here
# Apply it to methods like RequestHandler.produce_html()
def cacheable(html_generator):
    def decorator(self, *args, **kwargs):
        # self -> RequestHandler
        html, etag = HtmlCache.get_cached_or_make_new(self.request.path, lambda: html_generator(self, *args, **kwargs))
        serve = True
        if etag and 'If-None-Match' in self.request.headers:
            # etags are being sent via If-None-Match
            etags = [x.strip('" ') for x in self.request.headers['If-None-Match'].split(',')]
            if etag in etags:
                serve = False
        if etag:
            self.response.headers['ETag'] = '"%s"' % (etag,)
        #self.response.headers['Cache-Control'] = 'public, max-age=2592000'
        self.response.headers['Cache-Control'] = 'public, must-revalidate'
#        logging.debug('------------------------------------')
#        logging.debug('headers: %s' % self.request.headers)
#        logging.debug('If-None-Match: %s' % self.request.headers['If-None-Match'])
#        logging.debug('serve: %s' % serve)
        if serve:
            self.response.set_status(200)
            return html
        else:
            self.response.set_status(HTTP_304_NOT_MODIFIED)
            return ''
    return decorator

class DataStoreMeta(db.Model):
    updated = db.DateTimeProperty(auto_now=True, auto_now_add=True)
    #MEMCACHE_KEY = 'DataStoreMeta'

    @classmethod
    def __get_time_updated(cls):
        instance = db.Query(DataStoreMeta).get()
        if not instance:
            instance = DataStoreMeta()
            instance.put()
        return instance.updated

    @classmethod
    def update(cls):
        instance = db.Query(DataStoreMeta).get()
        if instance:
            instance.updated = datetime.datetime.now()
        else:
            instance = DataStoreMeta()
        instance.put()

    @classmethod
    def was_updated_after(cls, date):
        return cls.__get_time_updated() > date

# annotation designed exclusively for HtmlCache.get_cached_or_make_new()
def skip_ds_caching_for_admin(wrapped):
    def wrapper(cls, path, renderer):
        use_caching = True
        # disables caching for admin - regular users should not see admin interface
        use_caching = use_caching and not users.is_current_user_admin()
        # disables caching for dev server to see the changes applied
        #use_caching = use_caching and defs.PRODUCTION
        #use_caching = True
        if use_caching:
            return wrapped(cls, path, renderer)
        else:
            return renderer(), None
    return wrapper

class HtmlCache(db.Model):
    path = db.StringProperty(required=True, indexed=True)
    updated = db.DateTimeProperty(auto_now=True, auto_now_add=True)
    etag = db.StringProperty(required=True)
    app_version = db.StringProperty(required=True)
    html = db.TextProperty(required=True)

    @classmethod
    def __find(cls, path):
        q = db.Query(HtmlCache)
        q.filter('path = ', path)
        return q.get()

    @classmethod
    def __add(cls, path, html):
        object = HtmlCache(path=path,
            html=db.Text(html, defs.HTML_ENCODING),
            etag=hashlib.sha1(html).hexdigest(),
            app_version=defs.APP_VERSION)
        object.save()
        return object

    def __update(self, html):
        self.html = db.Text(html, defs.HTML_ENCODING)
        self.updated = datetime.datetime.now()
        self.etag = hashlib.sha1(html).hexdigest()
        self.app_version = defs.APP_VERSION
        self.put()

    @classmethod
    @skip_ds_caching_for_admin
    def get_cached_or_make_new(cls, path, renderer):
        # returns tuple: HTML and HTML's etag
        c = cls.__find(path=path)
        if c:
            if c.app_version != defs.APP_VERSION or DataStoreMeta.was_updated_after(c.updated):
                html = renderer()
                c.__update(html)
            else:
                html = c.html
        else:
            html = renderer()
            c = cls.__add(path, html)
        return html, c.etag

#logging.getLogger().setLevel(logging.DEBUG)