# -*- coding: utf-8 -*-

# this must go first - this var is to be checked in defs.py
# import os
# os.environ.setdefault('SERVER_PROFILE', 'DEVELOPMENT')

import os
import sys
import json
import codecs
import re
import cherrypy
from cherrypy.lib.static import serve_file
import jinja2
from jinja2 import Environment, FileSystemLoader

# import gen_static
# import utils

from common import Album
from common import format_size
from common import format_size_mb
from common import dict_of_lists
from common import write_file
from common import cut_start

DB_ROOT = 'DB\\narod'


def cat_title(cat_name):
    CAT_TITLES = {
        u'vocalists': u'Вокалисты',
        u'instrumental': u'Инструментальная музыка',
        u'ukraine': u'Украина',
        u'composers': u'Композиторы',
        u'via': u'ВИА',
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
        for file_short in os.listdir(self.db_root):
            if len(file_short) == 32:
                file_long = os.path.join(self.db_root, file_short)
                with codecs.open(file_long, 'r', 'utf-8') as f:
                    json_text = f.read()
                    json_obj = json.loads(json_text)
                    album = Album(json_obj)
                    self.__class__.augment_album_object(album)
                    self.albums[album['album_hash']] = album
                    self.categories.append(album['category'].lower(), album)
                    if album.has_key('total_size'):
                        self.total_size += album['total_size']
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
    def augment_album_object(cls, album):
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
          tail = album['title'][slash+1 : ]
          if tail.lower().startswith(artist.lower()):
            album['title'] = tail

        # filter out some stuff
        subs = [
            [  ur'\s*-\s*?.искография', '', re.I ],
            [  ur'\s*\(.искография\)', '', re.I ],
            [  ur'\s*FLAC$', '', re.I ],
            [  ur'\s+\dCD/CD', ' CD', re.I ], # '3CD/CD1' => 'CD1'
            # apply it among last ones
            [  ur'/', ' / ', re.I ],
        ]
        for sub in subs:
            album['title'] = re.sub(sub[0], sub[1], album['title'], flags=sub[2])

        # recognize audio format
        # before to cut off files extensions
        if len(album['tracks']) > 0:
            a_file_name = album['tracks'][0]['file_name']
            album['audio_format'] = os.path.splitext(a_file_name)[1][1:]

        # cut off file extensions
        for t in album['tracks']:
            t['file_name'] = os.path.splitext(t['file_name'])[0]


def generate_static_site():
    HTML_DIR = 'static_site'

    scg = StaticContentGenerator.get_instance(DB_ROOT)

    def save_page(file_short, content):
        file_long = os.path.join(HTML_DIR, file_short)
        print 'saving %s...' % file_long
        write_file(file_long, content)

    save_page('index.html', gen_index_page())
    save_page('search.html', gen_search_page())
    for cat_name in scg.categories.keys():
        save_page('%s.html' % cat_name, gen_category_page(cat_name))
    for album_hash in scg.albums.keys():
        save_page('%s.html' % album_hash, gen_album_page(album_hash))


def gen_index_page():
    scg = StaticContentGenerator.get_instance(DB_ROOT)
    albums = scg.albums.values()
    cats = []
    for cat_name, albums in scg.categories.items():
        cats.append({
            'name': cat_name,
            'title': cat_title(cat_name),
            'count': len(albums),
            #'albums': albums,
        })

    template_variables = {
        'scg': scg,
        'cats': cats,
        #'albums': albums,
    }
    return render_template('index.html', template_variables)


def gen_category_page(category):
    scg = StaticContentGenerator.get_instance(DB_ROOT)
    template_variables = {
        'scg': scg,
        'category': category,
        'category_title': cat_title(category),
        'albums': sorted(scg.categories[category], key=lambda album: album['path']),
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


def filter_search_input(s):
  ''' NB: do not joint the words because something unexpected results could be found '''
  s = re.sub(ur'[^0-9a-zA-Zа-яА-Я]+', ' ', s)
  s = s.strip()
  words = re.split(' +', s)
  return ' '.join(set(words)).lower()


class SearchableAlbum:
  def __init__(self, real_album):
    self.real_album = real_album
  def words(self):
    s = self.real_album['title']
    for track in self.real_album['tracks']:
      s += ' %s' % track['file_name']
    return filter_search_input(s)
  def title(self):
    return self.real_album['title']
  def html_location(self):
    return '/%s.html' % self.real_album['album_hash']

def gen_search_page():
  scg = StaticContentGenerator.get_instance(DB_ROOT)
  albums = sorted(scg.albums.values(), key=lambda album: album['title'].lower())
  albums = [ SearchableAlbum(album) for album in albums ]
  vars = {
    'scg': scg,
    'albums': albums,
  }
  return render_template('search.html', vars)


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

    # @cherrypy.expose
    # def page(self, page1):
    #     if type(page1) == str:
    #         m = re.match('(\d+)\.html', page1)
    #         if m:
    #             page1 = int(m.group(1))
    #         else:
    #             raise Exception('illegal page url %s' % page1)
    #     return utils.read_file(gen_static.generate_listing(page1))

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

    # @cherrypy.expose
    # def reset(self):
    #     gen_static.BlogMeta.reset()
    #     raise cherrypy.HTTPRedirect("/")

    # @cherrypy.expose
    # def tag(self, tag_name):
    #     tag_name = cut_mandatory_html_extension(tag_name)
    #     if tag_name == 'all':
    #         return utils.read_file(gen_static.generate_tag_cat())
    #     else:
    #         return utils.read_file(gen_static.generate_tag(tag_name))

    # @cherrypy.expose(alias="rss.xml")
    # def rss(self):
    #     response = cherrypy.response
    #     response.headers['Content-Type'] = 'text/xml'
    #     return utils.read_file(gen_static.generate_rss())

    @cherrypy.expose
    def static(self, *url_path, **url_params):
        file_path = os.path.join(current_dir, 'themes', 'static', *url_path)
        return serve_file(file_path)

    # @cherrypy.expose(alias='search.html')
    # def search(self, **params):
    #     return utils.read_file(gen_static.generate_search())

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'static':
        generate_static_site()
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root = Root()
        cherrypy.quickstart(root)