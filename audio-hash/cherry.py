# -*- coding: utf-8 -*-

import os
import sys
import json
import codecs
import re
import cherrypy
from cherrypy.lib.static import serve_file
from time import mktime
from datetime import datetime
import jinja2
from jinja2 import Environment, FileSystemLoader

# import gen_static
# import utils
import time

import utils
from utils import format_size
from utils import format_size_mb
from utils import dict_of_lists
import common
from common import Album
from common import write_file
from common import cut_start

DB_ROOT = 'DB\\narod'
#DB_ROOT = 'DB\\temp'


def cat_title(cat_name):
  CAT_TITLES = {
    u'baltic': u'Прибалты',
    u'vocalists': u'Вокалисты',
    u'instrumental': u'Инструментальная',
    u'ukraine': u'Укры',
    u'composers': u'Композиторы',
    u'via': u'ВИА',
    u'jazz': u'Джаз',
    u'georgia': u'Грузины',
    }
  return CAT_TITLES.get(cat_name, cat_name)


def typo(s):
  s = re.sub(u'^(\d+)(\s*)-', u'\\1\\2‒', s) # '01 -' ==> '01 ndash'
  s = re.sub(u'\s-\s', u' — ', s)            # ' - ' ==> mdash
  s = re.sub(u'-', u'‒', s)                  # '-' ==> ndash
  return s


def render_template(template_name, variables):
  env = Environment(loader=FileSystemLoader(['themes']), extensions=[])
  env.filters['format_size_mb'] = lambda value: format_size_mb(value)
  env.filters['format_size'] = lambda value: format_size(value)
  env.filters['typo'] = lambda value: typo(value)
  tpl = env.get_template(template_name)
  return tpl.render(variables)


class StaticContentGenerator:
  instance = None

  def __init__(self, db_root):
    self.db_root = db_root
    self.albums = {}
    self.categories = dict_of_lists()
    self.total_size = 0
    self.mtime = os.path.getmtime(db_root)
    for album in common.list_db_volume(self.db_root):
      self.__class__._augment_album_object(album)
      self.albums[album['album_hash']] = album
      self.categories.append(album['category'].lower(), album)
      if album.has_key('total_size'):
        self.total_size += album['total_size']
    self.albums_by_date = self.__class__._make_albums_by_date(self.albums.values())

  @classmethod
  def _make_albums_by_date(cls, albums):
    """
     return sorted list of dicts like {'date':'2012-01-01', 'albums':[]}
     they are grouped by date
     the most recent groupd goes first
    """
    aa = list(albums)
    aa = sorted(aa, key=lambda album: album['ctime'])
    last_date = None
    res = []
    for album in aa:
      tm = time.localtime(album['ctime'])
      this_date = time.strftime('%Y-%m-%d', tm)
      if not last_date:
        last_date = this_date
        res.append({'date':last_date, 'albums':[]})
      last_block = res[-1]
      if last_block['date'] == this_date:
        last_block['albums'].append(album)
      else:
        res.append({'date':this_date, 'albums':[album]})
        
    for block in res:
      block['albums'] = sorted(block['albums'], key=lambda album: album['title'])
    
    return res[::-1] # reversed

  def is_production(self):
    return IS_PRODUCTION
  
  @classmethod
  def get_instance(cls, db_root):
    ''' do not cache instance of this class but call this method each time instead
        caching only permittable inside a request handler
    '''
    #print 'GET_INSTANCE ------------------'
    refresh = cls.instance and cls.instance.mtime < os.path.getmtime(db_root)
    #print 'mtime: %s vs %s' % (mtime1, mtime2)
    if cls.instance is None or refresh:
      print 'refreshing data from db...'
      cls.instance = StaticContentGenerator(db_root)
    return cls.instance

  @classmethod
  def _augment_album_object(cls, album):
    title = album['path']

    title = cut_start(title, 'w:\\retro\\')
    title = cut_start(title, 'd:\\downloads\\sync\\')

    # try extract category like "georgia", "vocalists"
    category, rest = re.split('[\\\/]', title, 1)
    if category and re.match('[a-z]+', category) and rest:
      album['category'] = category
      title = rest
    else:
      album['category'] = 'misc'
      #album['category'] = cat_title(album['category'])

    album['title'] = title
    album['title'] = re.sub(r'\\', '/', album['title'])

    # 'John Doe/John Doe - Album' ==> 'John Doe - Album'
    slash = album['title'].find('/')
    if slash > 0:
      artist = album['title'][0:slash]
      tail = album['title'][slash + 1:]
      if tail.lower().startswith(artist.lower()):
        album['title'] = tail

    # filter out some stuff
    subs = [
      [ur'\s*-\s*?.искография', '', re.I],
      [ur'\s*\(.искография\)', '', re.I],
      [ur'\s*FLAC$', '', re.I],
      #[ur'\s+\dCD/CD', ' CD', re.I], # '3CD/CD1' => 'CD1'
      [ur'\s+(\d+)CD/CD(\d+)', u' \\1CD №\\2', re.I], # '3CD/CD1' => 'CD1'
      [ur'#', '/', re.I],
      # apply it among last ones
      [ur'/', ' / ', re.I],]
    for sub in subs:
      album['title'] = re.sub(sub[0], sub[1], album['title'], flags=sub[2])

    # try cut substring like [D-12345-60] from title
    album['title_short'] = album['title']
    m = re.match(ur'^(.+) \[(.{5,15})\](.*)$', album['title'])
    if m:
      album['title_short'] = m.group(1) + m.group(3)
      album['cat_no'] = m.group(2)

    # recognize audio format
    # before to cut off files extensions
    if len(album['tracks']) > 0:
      a_file_name = album['tracks'][0]['file_name']
      album['audio_format'] = os.path.splitext(a_file_name)[1][1:]

    # cut off file extensions
    for t in album['tracks']:
      t['file_name'] = os.path.splitext(t['file_name'])[0]

    # setup human friendly values like 44, 48, 96, 192
    for t in album['tracks']:
      if t.has_key('bits_per_sample'):
        t['khz'] = int(t['sample_rate'] / 1000)

    def get_cover_url(album):
      cover_file = os.path.join('covers', 'all', '%s.jpg' % album['album_hash'])
      if os.path.exists(cover_file):
        return '/covers/%s.jpg' % album['album_hash']
      else:
        return '/static/generic.jpg'

    album['cover_url'] = get_cover_url(album)


def generate_static_site():
  HTML_DIR = 'static_site'

  scg = StaticContentGenerator.get_instance(DB_ROOT)

  def save_page(file_short, content):
    file_long = os.path.join(HTML_DIR, file_short)
    print 'saving %s...' % file_long
    write_file(file_long, content)

  save_page('index.html', gen_index_page())
  save_page('search.html', gen_search_page())
  save_page('comments.html', gen_feedback_page())
  save_page('updates.html', gen_updates_page())
  for cat_name in scg.categories.keys():
    save_page('%s.html' % cat_name, gen_category_page(cat_name))
  for album_hash in scg.albums.keys():
    save_page('%s.html' % album_hash, gen_album_page(album_hash))


def gen_index_page():
  scg = StaticContentGenerator.get_instance(DB_ROOT)
  cats = [
    {
      'name': cat_name,
      'title': cat_title(cat_name),
      'count': len(albums),
    }
    for cat_name, albums in scg.categories.items()
  ]
  cats = sorted(cats, key=lambda cat: cat['title'].lower())
  template_variables = {
    'scg': scg,
    'cats': cats,
    'up_date': datetime.fromtimestamp(time.mktime(time.localtime())),
    }
  return render_template('index.html', template_variables)


def gen_category_page(category):
  scg = StaticContentGenerator.get_instance(DB_ROOT)
  sort_by_title = lambda album: album['title']
  template_variables = {
    'scg': scg,
    'category': category,
    'category_title': cat_title(category),
    'albums': sorted(scg.categories[category], key=sort_by_title),
    }
  return render_template('category.html', template_variables)


def gen_album_page(album_hash):
  scg = StaticContentGenerator.get_instance(DB_ROOT)
  album = scg.albums[album_hash]
  #return 'album %s found %s' % (album_hash, album['path'])
  template_variables = {
    'scg': scg,
    'album': album,
    'category': album['category'],
    'category_title': cat_title(album['category']),
    }
  return render_template('album.html', template_variables)


def _filter_search_input(s):
  ''' NB: do not join the words because unexpected results could be found '''
  s = utils.normalize_unicode_except_cyrillic(s)
  s = re.sub(ur'[^0-9a-zA-Zа-яА-Я]+', ' ', s)
  s = s.strip()
  words = re.split('\s+', s)
  s = ' '.join(set(words)).lower()
  return s


class SearchableAlbum:
  def __init__(self, real_album):
    self.real_album = real_album

  def words(self):
    s = self.real_album['title']
    for track in self.real_album['tracks']:
      s += ' %s' % track['file_name']
    return _filter_search_input(s)

  def title(self):
    return self.real_album['title']

  def html_location(self):
    return '/%s.html' % self.real_album['album_hash']


def gen_search_page():
  scg = StaticContentGenerator.get_instance(DB_ROOT)
  albums = sorted(scg.albums.values(), key=lambda album: album['title'].lower())
  albums = [SearchableAlbum(album) for album in albums]
  vars = {
    'scg': scg,
    'albums': albums,
    }
  return render_template('search.html', vars)


def gen_feedback_page():
  scg = StaticContentGenerator.get_instance(DB_ROOT)
  template_variables = {
    'scg': scg,
    }
  return render_template('feedback.html', template_variables)


def gen_updates_page():
  scg = StaticContentGenerator.get_instance(DB_ROOT)
  template_variables = {
    'scg': scg,
    }
  return render_template('updates.html', template_variables)


def cut_mandatory_html_extension(s):
  m = re.match('(.+)\.html', s, re.IGNORECASE)
  if m:
    return m.group(1)
  else:
    raise cherrypy.NotFound()


class Root:
  @cherrypy.expose
  def index(self):
    return gen_index_page()

  @cherrypy.expose
  def default(self, path):
    scg = StaticContentGenerator.get_instance(DB_ROOT)
    slug = cut_mandatory_html_extension(path)
    if scg.albums.has_key(slug):
      return gen_album_page(slug)
    elif scg.categories.has_key(slug):
      return gen_category_page(slug)
    else:
      raise cherrypy.NotFound()

  @cherrypy.expose(alias="search.html")
  def search(self):
    return gen_search_page()

  @cherrypy.expose(alias="comments.html")
  def search(self):
    return gen_feedback_page()

  @cherrypy.expose(alias="updates.html")
  def search(self):
    return gen_updates_page()

  @cherrypy.expose
  def static(self, *url_path, **url_params):
    file_path = os.path.join(current_dir, 'themes', 'static', *url_path)
    return serve_file(file_path)

  @cherrypy.expose
  def covers(self, *url_path, **url_params):
    file_path = os.path.join(current_dir, 'covers', 'all', *url_path)
    return serve_file(file_path)

if __name__ == '__main__':
  if len(sys.argv) == 2 and sys.argv[1] == 'static':
    IS_PRODUCTION = True
    generate_static_site()
  else:
    IS_PRODUCTION = False
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root = Root()
    cherrypy.quickstart(root)