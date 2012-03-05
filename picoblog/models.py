import datetime
import sys
from google.appengine.api import memcache

from google.appengine.ext import db

import utils

FETCH_THEM_ALL_COMMENTS = 100
FETCH_ALL_TAGS = 1000
FETCH_ALL_TAGS_FOR_TAG_CLOUD = 2000 # there are about 150 tags in Opera
FETCH_ALL_SLUGS = 500
MAX_ARTICLES_PER_DAY = 20

########################################################

class ArticleTag(db.Model):
    name = db.StringProperty(required=True, indexed=True)
    counter = db.IntegerProperty(default=0, indexed=True)
    category = db.StringProperty(default='', indexed=True)

    @classmethod
    def tags_updated_for_article(cls, tags_was, tags_now):
        tags_was = set(tags_was)
        tags_now = set(tags_now)

        cls.__modify_tags_counters(tags_was - tags_now, lambda cnt: cnt - 1)
        cls.__modify_tags_counters(tags_now - tags_was, lambda cnt: cnt + 1)
        pass

    @classmethod
    def article_removed(cls, tags_was):
        cls.__modify_tags_counters(set(tags_was), lambda cnt: cnt - 1)
        pass

    @classmethod
    def __modify_tags_counters(cls, tags, modifying_function):
        for tag in tags:
            tag_obj = db.get(tag) if type(tag) == db.Key else ArticleTag.get_by_name(tag, create_on_demand=True)
            new_value = modifying_function(tag_obj.counter)
            new_value = new_value if new_value >= 0 else 0
            if new_value != tag_obj.counter:
                tag_obj.counter = new_value
                tag_obj.save()

    @classmethod
    def get_by_name(cls, tag_name, create_on_demand = False):
        utils.assert_type(tag_name, unicode)
        tag_obj = db.Query(ArticleTag).filter('name', tag_name).get()
        if not tag_obj and create_on_demand:
            tag_obj = ArticleTag(name=tag_name, counter=0)
            tag_obj.save()
        return tag_obj

    @classmethod
    def get_by_key(cls, tag_key, create_on_demand = False):
        tag_obj = db.get(tag_key)
        if not tag_obj and create_on_demand:
            raise Exception('Cannot find a tag by key %s' % tag_key)
        return tag_obj

    @classmethod
    def get_keys_by_names_creating(cls, tag_names):
        return [ cls.get_by_name(tag_name, True).key() for tag_name in tag_names ]

    @classmethod
    def fetch_all(cls):
        return db.Query(cls)\
                 .filter('counter > ', 0)\
                 .fetch(FETCH_ALL_TAGS_FOR_TAG_CLOUD)

########################################################

class TagCloud():
    """
    All tags in memory, 2-3 KB
    """
    KEY = 'region-tag-cloud'
    @classmethod
    def get(cls):
        value = memcache.get(cls.KEY)
        if not value or len(value) == 0:
            value = cls.__make_cloud()
            # todo: keep it forever but don't forget to reset (patch) memcache when a tag changed in datastore
            memcache.set(cls.KEY, value, utils.hours(1).seconds())
        return value
    @classmethod
    def reset(cls):
        memcache.delete(cls.KEY)
    @classmethod
    def __make_cloud(cls):
        #raise Exception('__make_cloud')
        tag_cloud = {}
        for tag in ArticleTag.fetch_all():
            tag_cloud[tag.name] = tag.counter
        return tag_cloud

########################################################

class Article(db.Model):

    id = db.IntegerProperty()
    title = db.StringProperty(required=True, indexed=False)
    body = db.TextProperty(indexed=False)
    published_date = db.DateTimeProperty(auto_now_add=True, indexed=True)
    tags = db.ListProperty(db.Key)
    draft = db.BooleanProperty(required=True, default=False)

    def fetch_comments(self):
        return Comment.get_for_article(self)

    @classmethod
    def get(cls, id):
        q = db.Query(Article)
        q.filter('id = ', id)
        return q.get()

    @classmethod
    def query_all(cls):
        return db.Query(Article).order('-published_date')

    @classmethod
    def query_published(cls):
        return cls.query_all()\
                  .filter('draft = ', False)\
                  .order('-published_date')

    @classmethod
    def all_for_month_query(cls, year, month):
        start_date = datetime.date(year, month, 1)
        if start_date.month == 12:
            next_year = start_date.year + 1
            next_month = 1
        else:
            next_year = start_date.year
            next_month = start_date.month + 1

        end_date = datetime.date(next_year, next_month, 1)
        return Article.published_query()\
                       .filter('published_date >=', start_date)\
                       .filter('published_date <', end_date)\
                       .order('-published_date')

    @classmethod
    def query_for_tag_name(cls, tag_name):
        tag = ArticleTag.get_by_name(tag_name) # todo: optimization: select a key not object
        key = tag.key() if tag else None
        q = Article.query_published().filter('tags', key)
        #raise Exception(q._get_query())
        return q

    @classmethod
    def convert_string_tags(cls, tag_names):
        new_tags = []
        if len(tag_names) > 0: assert type(tag_names[0]) == str or type(tag_names[0]) == unicode
        return ArticleTag.get_keys_by_names_creating(tag_names)
#        for t in tag_names:
#            if type(t) == db.Category:
#                new_tags.append(t)
#            else:
#                new_tags.append(db.Category(unicode(t)))
#        return new_tags

    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return '[%s] %s' %\
               (self.published_date.strftime('%Y/%m/%d %H:%M'), self.title)

    def get_tag_objects(self):
        return db.get(self.tags)

    def get_tag_names(self):
        return [ tag.name for tag in self.get_tag_objects() ]

    def create_uniq_id(self):
        # TODO this could be rewritten with max(id)+1 for current day's articles
        for i in xrange(MAX_ARTICLES_PER_DAY):
            unique = "" if i == 0 else str(i)
            id_str = "%04d%02d%02d%s" % (int(self.published_date.year),
                                         int(self.published_date.month),
                                         int(self.published_date.day),
                                         unique)
            id = int(id_str)
            if not Article.get(id):
                return id
        raise Exception("Cannot create an article id for date %s after %d tries" % (self.published_date, MAX_ARTICLES_PER_DAY))

    def delete(self, **kwargs):
        prev_tags = self.tags
        super(Article, self).delete(**kwargs)
        ArticleTag.article_removed(prev_tags)

    def save(self):
        previous_version = Article.get(self.id)
        previous_tags = previous_version.tags if previous_version else []

        ArticleTag.tags_updated_for_article(previous_tags, self.tags)
        
        if previous_version and previous_version.draft and (not self.draft):
            # Event: switching from draft to published.
            # Action: update the timestamp.
            self.published_date = datetime.datetime.now()

        if self.is_saved():
            self.put()
        else:
            id = self.create_uniq_id()
            self.put()
            self.id = id
            self.put()


########################################################

class Comment(db.Model):

    id = db.IntegerProperty()
    article = db.ReferenceProperty(Article)
    blog_owner = db.BooleanProperty(required=True, default=False)
    author = db.StringProperty() # Could be None for anonymous users of myopera
    text = db.TextProperty(required=True)
    published_date = db.DateTimeProperty(auto_now_add=True)
    #replied_comment = db.SelfReferenceProperty()
    replied_comment_id = db.IntegerProperty()

    @classmethod
    def get(cls, id):
        q = db.Query(Comment)
        q.filter('id = ', id)
        return q.get()

    @classmethod
    def get_for_article(cls, article):
        return db.Query(Comment)\
                 .filter("article = ", article)\
                 .order('replied_comment_id')\
                 .order('published_date')\
                 .fetch(FETCH_THEM_ALL_COMMENTS)

    def save(self):
        if self.is_saved():
            self.put()
        else:
            self.put()
            self.id = self.key().id()
            if not self.replied_comment_id:
                self.replied_comment_id = self.id
            self.put()

########################################################

# generated images cache
# such entries could be cleaned out without any problems
class FontRenderCache(db.Model):
    hash = db.IntegerProperty(required=True, indexed=True)
    width = db.IntegerProperty(required=True, indexed=False)
    height = db.IntegerProperty(required=True, indexed=False)
    render = db.BlobProperty(required=True, indexed=False)
    @classmethod
    def calc_hash(cls, font_name, font_size, text):
        return ("%s%s%s" % (font_name, font_size, text)).__hash__()
    @classmethod
    def find(cls, font_name, font_size, text):
        q = db.Query(FontRenderCache)
        q.filter('hash = ', cls.calc_hash(font_name, font_size, text))
        return q.get()
    @classmethod
    def insert_new(cls, font_name, font_size, text, image):
        obj = FontRenderCache(hash = cls.calc_hash(font_name, font_size, text),
                              width = image.get_width(),
                              height = image.get_height(),
                              render = image.get_data_as_string())
        obj.save()
    def save(self):
        self.put()

########################################################

class Slug(db.Model):
    slug = db.StringProperty(required=True, indexed=True)
    article = db.ReferenceProperty(Article, required=True)
    added_date = db.DateTimeProperty(auto_now_add=True, indexed=True)
    
    @classmethod
    def find_article_by_slug(cls, slug_string):
        q = db.Query(Slug)
        q.filter('slug = ', slug_string)
        return q.get()

    @classmethod
    def get_slugs_for_article(cls, article):
        q = db.Query(Slug)
        q.filter('article = ', article)
        q.order('-added_date') # recent entries first
        return q.fetch(FETCH_ALL_SLUGS)
        
    @classmethod
    def get_default_slug_for_article(cls, article):
        slugs = cls.get_slugs_for_article(article)
        if len(slugs) == 0:
            raise Exception('cannot find any slug for article %s' % article)
        return slugs[0]
    
    @classmethod
    def insert_new(cls, slug, article):
        if type(slug) != unicode and type(slug) != str:
            raise Exception('param slug is of bad type: %s' % type(slug))
        existing = cls.find_article_by_slug(slug_string=slug)
        if existing:
            raise Exception('article with slug "%s" already exists' % (slug))
        else:
            obj = Slug(slug=slug, article=article)
            obj.save()
            return obj

    def save(self):
        self.put()
