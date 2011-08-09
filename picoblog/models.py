import datetime
import sys

from google.appengine.ext import db

FETCH_THEM_ALL_COMMENTS = 100
FETCH_ALL_TAGS = 1000
MAX_ARTICLES_PER_DAY = 20

class TagCounter(db.Model):
    name = db.StringProperty(required=True, indexed=True)
    counter = db.IntegerProperty(default=0, indexed=True)

    @classmethod
    def tags_updated_for_article(cls, tags_was, tags_now):
        tags_was = set(tags_was)
        tags_now = set(tags_now)
        cls.__modify_tags_counters(tags_was - tags_now, lambda cnt: cnt - 1)
        cls.__modify_tags_counters(tags_now - tags_was, lambda cnt: cnt + 1)

    @classmethod
    def article_removed(cls, tags_was):
        cls.__modify_tags_counters(set(tags_was), lambda cnt: 0)

    @classmethod
    def __modify_tags_counters(cls, tag_names, modifying_function):
        for tag_name in tag_names:
            tag = TagCounter.get_by_name(tag_name, create_on_demand=True)
            tag.counter = modifying_function(tag.counter)
            if tag.counter < 0:
                tag.counter = 0
            tag.save()

    @classmethod
    def get_by_name(cls, tag_name, create_on_demand = False):
        tag_counter = db.Query(TagCounter).filter('name', tag_name).get()
        if not tag_counter and create_on_demand:
            tag_counter = TagCounter(name=tag_name, counter=0)
            tag_counter.save()
        return tag_counter

    @classmethod
    def create_tag_cloud(cls):
        tag_cloud = {}
        tags = db.Query(TagCounter).filter("counter > ", 0).fetch(FETCH_ALL_TAGS)
        for tag in tags:
            tag_cloud[tag.name] = tag.counter
        return tag_cloud

class Article(db.Model):

    id = db.IntegerProperty()
    title = db.StringProperty(required=True, indexed=False)
    #title_slug = db.StringProperty(required=True)
    body = db.TextProperty(indexed=False)
    published_date = db.DateTimeProperty(auto_now_add=True, indexed=True)
    tags = db.ListProperty(db.Category)
    draft = db.BooleanProperty(required=True, default=False)

    def get_comments(self):
        return self.comment_set.fetch(FETCH_THEM_ALL_COMMENTS)

    @classmethod
    def get(cls, id):
        q = db.Query(Article)
        q.filter('id = ', id)
        return q.get()

    #    @classmethod
#    def published_query(cls):
#        q = db.Query(Article)
#        q.filter('draft = ', False)
#        return q
#
#    @classmethod
#    def published(cls):
#        return Article.published_query()\
#                      .order('-published_date')\
#                      .fetch(FETCH_THEM_ALL)

    @classmethod
    def query_all(cls):
        return db.Query(Article).order('-published_date')

    @classmethod
    def query_published(cls):
        return cls.query_all()\
                  .filter('draft = ', False)\
                  .order('-published_date')

#    @classmethod
#    def published_query(cls):
#        return Article.published_query()\
#                      .filter('draft = ', False)\
#                      .order('-published_date')
#
#    @classmethod
#    def get_all_tags(cls):
#        """
#        Return all tags, as TagCount objects, optionally sorted by frequency
#        (highest to lowest).
#        """
#        tag_counts = {}
#        for article in Article.published():
#            for tag in article.tags:
#                tag = unicode(tag)
#                try:
#                    tag_counts[tag] += 1
#                except KeyError:
#                    tag_counts[tag] = 1
#        return tag_counts
#
#    @classmethod
#    def get_all_datetimes(cls):
#        dates = {}
#        for article in Article.published():
#            date = datetime.datetime(article.published_date.year,
#                                     article.published_date.month,
#                                     article.published_date.day)
#            try:
#                dates[date] += 1
#            except KeyError:
#                dates[date] = 1
#        return dates

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
    def query_for_tag(cls, tag):
        return Article.query_published() \
                      .filter('tags', tag)

    @classmethod
    def convert_string_tags(cls, tags):
        new_tags = []
        for t in tags:
            if type(t) == db.Category:
                new_tags.append(t)
            else:
                new_tags.append(db.Category(unicode(t)))
        return new_tags

    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return '[%s] %s' %\
               (self.published_date.strftime('%Y/%m/%d %H:%M'), self.title)

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
        TagCounter.article_removed(prev_tags)

    def save(self):
        previous_version = Article.get(self.id)
        previous_tags = previous_version.tags if previous_version else []

        TagCounter.tags_updated_for_article(previous_tags, self.tags)

        if previous_version and previous_version.draft and (not self.draft):
            # Going from draft to published. Update the timestamp.
            self.published_date = datetime.datetime.now()

        if self.is_saved():
            self.put()
        else:
            id = self.create_uniq_id()
            self.put()
            self.id = id
            self.put()


class Comment(db.Model):

    id = db.IntegerProperty()
    article = db.ReferenceProperty(Article)
    blog_owner = db.BooleanProperty(required=True, default=False)
    author = db.StringProperty() # Could be None for anonymous users of myopera
    text = db.TextProperty(required=True)
    published_date = db.DateTimeProperty(auto_now_add=True)
    #replied_comment = db.SelfReferenceProperty()
    replied_comment_id = db.IntegerProperty()
    image = db.BlobProperty()
    
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
        self.image = '12345'
        if self.is_saved():
            self.put()
        else:
            self.put()
            self.id = self.key().id()
            if not self.replied_comment_id:
                self.replied_comment_id = self.id
            self.put()

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
