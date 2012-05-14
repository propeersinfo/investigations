import os
import cherrypy
from cherrypy.lib.static import serve_file
import gen_static
import utils


class Root:
    @cherrypy.expose
    def index(self):
        return self.page(1)

    @cherrypy.expose
    def page(self, page1):
        page1 = int(page1)
        return utils.read_file(gen_static.generate_listing(page1))

    @cherrypy.expose
    def default(self, slug):
        return utils.read_file(gen_static.generate_article(slug))

    @cherrypy.expose
    def reset(self):
        gen_static.BlogMeta.reset()
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def tag(self, tag_name):
        return utils.read_file(gen_static.generate_tag(tag_name))

    @cherrypy.expose
    def static(self, *url_path, **url_params):
        file_path = os.path.join(current_dir, 'themes', 'grid', 'static', *url_path)
        return serve_file(file_path)

    @cherrypy.expose
    def search(self, **params):
        return utils.read_file(gen_static.generate_search())

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root = Root()
    cherrypy.quickstart(root)