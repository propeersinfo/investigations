# -*- coding: utf-8 -*-
import codecs
import logging
import hashlib
import random
import re
import unicodedata
import Cookie
import datetime
import time

import defs



# def get_class_that_defined_method(method):
#    obj = method.im_self
#    for cls in inspect.getmro(method.im_class):
#        if method.__name__ in cls.__dict__:
#            return cls
#    return None

#def deprecated(wrapped):
#    def wrapper(*args, **kwargs):
#        #raise Exception('function: %s' % (wrapped.im_class,))
#        raise Exception('function %s %s is deprecated %s' % (wrapped, wrapped.__name__, ''))
#    return wrapper


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""

    def new_func(*args, **kwargs):
        raise Exception("Call to deprecated function %s" % (func.__name__,))

    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func


class PageLoadTime():
    def __init__(self):
        self.start_time = datetime.datetime.now()

    def print_time(self, out):
        delta = datetime.datetime.now() - self.start_time
        out.write('<p class="page-generation-time">Page generated for %d:%03d</p>' % (
            delta.seconds, delta.microseconds / 1000))


# Examples:
# http://localhost/_ah/admin/datastore/edit?key=ahRkZXZ-c292aWV0cmFyZWdyb292ZXIPCxIHQXJ0aWNsZRjh1AEM&kind=Article&next=http%3A//localhost/_ah/admin/datastore%3Fkind%3DArticle
# https://appengine.google.com/datastore/edit?app_id=sovietraregroove&version_id=1.357588515741945103&key=ahBzb3ZpZXRyYXJlZ3Jvb3Zlcg8LEgdBcnRpY2xlGPO7AQw
def get_ds_object_edit_link(ds_object):
    key = ds_object.key()
    app_id = 'sovietraregroove'
    if defs.PRODUCTION:
        s = 'https://appengine.google.com/datastore/edit?app_id=%s&version_id=%s&key=%s' % (
            app_id, defs.APP_VERSION, key)
    else:
        s = '%s/_ah/admin/datastore/edit?key=%s&kind=Article' % (defs.CANONICAL_BLOG_URL, key)
    return s


def slugify(s):
    if type(s) == str:
        s = unicode(s)
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').lower()
    s = re.sub("[']", '', s)  # remove some chars
    s = re.sub('[^a-zA-Z0-9-]+', '-', s)  # replace the rest with '-'
    s = re.sub('--+', '-', s)  # eliminate '--'
    s = s.strip('-')
    return s


def get_article_path(article):
    return '/%s' % (article.slug,)


def get_article_url(article):
    return defs.CANONICAL_BLOG_URL + get_article_path(article)


def get_article_guid(article):
    #return '/article/%s' % (article.id)
    return get_article_url(article)


def set_cookie(response, key, value):
    c = Cookie.SimpleCookie()
    c[key] = value
    c[key]["expires"] = "Sun, 31-May-2020 23:59:59 GMT"
    c[key]["path"] = "/"
    response.headers.add_header('Set-Cookie', c[key].OutputString())


def set_unicode_cookie(response, key, value):
    c = Cookie.SimpleCookie()
    c[key] = value.encode('unicode-escape')
    c[key]["expires"] = "Sun, 31-May-2020 23:59:59 GMT"
    c[key]["path"] = "/"
    response.headers.add_header('Set-Cookie', c[key].OutputString())


def get_unicode_cookie(request, key, default_value):
    def unescape(s):
        m = re.match(r'^"(.*)"$', s)
        s = m.group(1) if m else s
        return s.replace("\\\\", "\\")

    if request.cookies.has_key(key):
        return unescape(request.cookies[key]).decode('unicode-escape')
    else:
        return default_value


#def read_file(file):
#    full = os.path.join(os.path.split(__file__)[0], file)
#    return open(full).read()

def read_file(path, charset="utf-8"):
    f = codecs.open(path, "r", charset)
    try:
        return f.read()
    finally:
        f.close()


def write_file(path, content):
    if type(content) == unicode:
        content = unicode(content).encode('utf-8')
    elif type(content) == str:
        pass
    else:
        raise Exception('content is of a non-tested type %s' % type(content))

    f = codecs.open(path, "wb")
    try:
        return f.write(content)
    finally:
        f.close()


class TimePeriod():
    def __init__(self, seconds):
        self.__seconds = seconds

    def seconds(self):
        return self.__seconds


# Usage: utils.hours(1).seconds()
def hours(hours):
    tp = TimePeriod(hours * 60 * 60)
    return tp


if __name__ == '__main__':
    titles = [u'About the cat / Про кота (1985)', u'A dear boy (1974) - Part 1', u'Theme from Rocky\'s cover',
              u'75 / ВИА 75 (1979)']
    for t in titles:
        print slugify(t)


def assert_type(object, expected_type):
    if not isinstance(object, expected_type):
        raise Exception('Expected type: %s. Actual: %s' % (expected_type, type(object)))


def setup_log_ds_queries():
    #counter = 0

    from google.appengine.api import apiproxy_stub_map
    from google.appengine.datastore import datastore_index

    def db_log(model, call, details=''):
        #if model == 'Article':
        #global counter
        #if counter == 1: raise Exception('%s' % 'stack trace')
        logging.debug('~~~~~~~~~~~~~~~~~~~~~~~~')
        logging.debug('~~ DB_LOG: %s @ %s (%s)', call, model, details)
        logging.debug('~~ %d' % counter)
        #counter += 1
        #if counter >= 2: counter = 0

    """Apply a hook to app engine that logs db statistics."""

    def model_name_from_key(key):
        return key.path().element_list()[0].type()

    def hook(service, call, request, response):
        assert service == 'datastore_v3'
        if call == 'Put':
            for entity in request.entity_list():
                db_log(model_name_from_key(entity.key()), call)
        elif call in ('Get', 'Delete'):
            for key in request.key_list():
                db_log(model_name_from_key(key), call)
        elif call == 'RunQuery':
            kind = datastore_index.CompositeIndexForQuery(request)[1]
            db_log(kind, call)
        else:
            db_log(None, call)

    apiproxy_stub_map.apiproxy.GetPreCallHooks().Append(
        'db_log', hook, 'datastore_v3')


def dump_execution_time(wrapped):
    def decorator(*args, **kwargs):
        start_time = datetime.datetime.now()
        rv = wrapped(*args, **kwargs)
        dt = datetime.datetime.now() - start_time
        logging.debug('***** %s() took %d:%03d' % (wrapped.__name__, dt.seconds, dt.microseconds / 1000))
        return rv

    return decorator


logging.getLogger().setLevel(logging.DEBUG)


def get_seconds_since_epoch():
    float = time.mktime(time.gmtime())
    return int(float)


def split_and_strip_tags(s, delim=','):
    lst = s.split(delim)
    lst = map(lambda s: s.strip(), lst)
    lst = filter(lambda tag: len(tag) > 0, lst)
    lst = set(lst)
    for i in lst:
        assert len(i) > 0
    return lst


def split_list_into_chunks(src, chunk_size):
    return [src[i:i + chunk_size] for i in range(0, len(src), chunk_size)]


def limit(lst, limit):
    if limit > len(lst):
        limit = len(lst)
    return lst[0:limit]


def average_number(numbers):
    return reduce(lambda sum, len: sum + len, numbers, 0)


#def mkdirs(path):
#    try:
#        os.makedirs(path)
#    except OSError as exc: # Python >2.5
#        if exc.errno == errno.EEXIST:
#            pass
#        else: raise

def get_article_path(article):
    assert type(article) is not str
    #import gen_static
    #assert article.__class__ == gen_static.ArticleDataStoreMock, article.__class__
    #assert isinstance(article, gen_static.ArticleDataStoreMock)
    return '/%s.html' % article.slug


def get_article_url(article):
    assert type(article) is not str
    #import gen_static
    #assert article.__class__ == gen_static.ArticleDataStoreMock, article.__class__
    return '%s/%s.html' % (defs.CANONICAL_BLOG_URL, article.slug)


class UTC(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return datetime.timedelta(0)


class ConstantOffsetTimeZone(datetime.tzinfo):
    def __init__(self, utc_offset):
        super(ConstantOffsetTimeZone, self).__init__()
        #assert utc_offset.seconds % 60 == 0, 'actual seconds: %s' % utc_offset.seconds
        #assert utc_offset.microseconds == 0
        #raise Exception('utc_offset: %s %s' % (utc_offset.seconds, utc_offset.microseconds))
        self.utc_offset = utc_offset

    def utcoffset(self, dt):
        return self.utc_offset

    def tzname(self, dt):
        assert False, 'tzname could not be defined, do not use formatting %%Z'

    def dst(self, dt):
        return datetime.timedelta(0)


def try_clone_naive_local_datetime_with_timezone_info(dt):
    if dt.tzinfo:
        return dt
    else:
        #utc_offset = datetime.datetime.now() - datetime.datetime.utcnow()
        utc_offset = datetime.timedelta(hours=defs.DEFAULT_LOCAL_TIMEZONE_OFFSET)
        aware = dt.replace(tzinfo=ConstantOffsetTimeZone(utc_offset))
        return aware


def file_md5_hex(filename):
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()


def hexdigest(s):
    md5 = hashlib.md5()
    md5.update(s)
    return md5.hexdigest()


def pick_pseudo_random_elements(random_seed, source_list, num_elements):
    if len(source_list) <= 0 or num_elements <= 0:
        return []
    if num_elements > len(source_list):
        num_elements = len(source_list)

    rnd = random.Random(random_seed)
    res = []
    indices_used = set()
    for i in range(0, num_elements):
        src_idx = 0
        while True:
            src_idx = int(len(source_list) * rnd.random())
            if not src_idx in indices_used:
                indices_used.add(src_idx)
                break
        # print "%s" % (src_idx)
        res.append(source_list[src_idx])
    return res
