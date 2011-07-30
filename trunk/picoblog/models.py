import datetime
import sys

from google.appengine.ext import db

FETCH_THEM_ALL = 12345
FETCH_THEM_ALL_COMMENTS = 100
MAX_ARTICLES_PER_DAY = 10

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
    def get_all(cls):
        q = db.Query(Article)
        q.order('-published_date')
        return q.fetch(FETCH_THEM_ALL)

    @classmethod
    def get(cls, id):
        q = db.Query(Article)
        q.filter('id = ', id)
        return q.get()

    @classmethod
    def published_query(cls):
        q = db.Query(Article)
        q.filter('draft = ', False)
        return q

    @classmethod
    def published(cls):
        return Article.published_query()\
                      .order('-published_date')\
                      .fetch(FETCH_THEM_ALL)

    @classmethod
    def published_no_fetch(cls):
        return Article.published_query()\
                      .order('-published_date')

    @classmethod
    def get_all_tags(cls):
        """
        Return all tags, as TagCount objects, optionally sorted by frequency
        (highest to lowest).
        """
        tag_counts = {}
        for article in Article.published():
            for tag in article.tags:
                tag = unicode(tag)
                try:
                    tag_counts[tag] += 1
                except KeyError:
                    tag_counts[tag] = 1

        return tag_counts

    @classmethod
    def get_all_datetimes(cls):
        dates = {}
        for article in Article.published():
            date = datetime.datetime(article.published_date.year,
                                     article.published_date.month,
                                     article.published_date.day)
            try:
                dates[date] += 1
            except KeyError:
                dates[date] = 1

        return dates

    @classmethod
    def all_for_month(cls, year, month):
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
                       .order('-published_date')\
                       .fetch(FETCH_THEM_ALL)

    @classmethod
    def all_for_tag(cls, tag):
        return Article.published_query()\
                      .filter('tags = ', tag)\
                      .order('-published_date')\
                      .fetch(FETCH_THEM_ALL)

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

    def save(self):
        previous_version = Article.get(self.id)
        try:
            draft = previous_version.draft
        except AttributeError:
            draft = False

        if draft and (not self.draft):
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
    author = db.StringProperty() # Could be None for anonymouses of myopera
    text = db.TextProperty(required=True)
    published_date = db.DateTimeProperty(auto_now_add=True)
    
    @classmethod
    def get(cls, id):
        q = db.Query(Comment)
        q.filter('id = ', id)
        return q.get()

    def save(self):
        if self.is_saved():
            self.put()
        else:
            self.put()
            self.id = self.key().id()
            self.put()