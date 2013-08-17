# this must go first - this var is to be checked in defs.py
import os
os.environ.setdefault('SERVER_PROFILE', 'DEVELOPMENT')

import re
import cherrypy
from cherrypy.lib.static import serve_file

import gen_static
import utils

def cut_mandatory_html_extension(s):
    m = re.match('(.+)\.html', s, re.IGNORECASE)
    if m:
        return m.group(1)
    else:
        raise cherrypy.NotFound()

class Root:
    @cherrypy.expose
    def index(self):
        return self.page(1)

    @cherrypy.expose
    def page(self, page1):
        if type(page1) == str:
            m = re.match('(\d+)\.html', page1)
            if m:
                page1 = int(m.group(1))
            else:
                raise Exception('illegal page url %s' % page1)
        return utils.read_file(gen_static.generate_listing(page1))

    @cherrypy.expose
    def default(self, path):
        slug = cut_mandatory_html_extension(path)
        return utils.read_file(gen_static.generate_article(slug))

    @cherrypy.expose
    def reset(self):
        gen_static.BlogMeta.reset()
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def tag(self, tag_name):
        tag_name = cut_mandatory_html_extension(tag_name)
        if tag_name == 'all':
            return utils.read_file(gen_static.generate_tag_cat())
        else:
            return utils.read_file(gen_static.generate_tag(tag_name))

    @cherrypy.expose(alias="rss.xml")
    def rss(self):
        response = cherrypy.response
        response.headers['Content-Type'] = 'text/xml'
        return utils.read_file(gen_static.generate_rss())

    @cherrypy.expose
    def static(self, *url_path, **url_params):
        file_path = os.path.join(current_dir, 'themes', 'grid', 'static', *url_path)
        return serve_file(file_path)

    @cherrypy.expose(alias='search.html')
    def search(self, **params):
        return utils.read_file(gen_static.generate_search())

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root = Root()
    cherrypy.quickstart(root)