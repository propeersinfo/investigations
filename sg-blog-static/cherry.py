import os
import cherrypy
from cherrypy.lib.static import serve_file
import gen_static
import utils


class Root:
    @cherrypy.expose
    def index(self):
        #html_file = gen_static.generate_listing(1)
        #return utils.read_file(html_file)
        return self.page(1)

    @cherrypy.expose
    def page(self, page1):
        html_file = gen_static.generate_listing(int(page1))
        return utils.read_file(html_file)

    @cherrypy.expose
    def default(self, slug):
        gen_static.generate_article(slug)
        html_file = os.path.join(os.path.dirname(__file__), 'html', slug)
        return utils.read_file(html_file)

    @cherrypy.expose
    def tag(self, tag_name):
        gen_static.generate_tag_page(tag_name)
        html_file = os.path.join(os.path.dirname(__file__), 'html', 'tag', tag_name)
        return utils.read_file(html_file)

    @cherrypy.expose
    def static(self, *url_path, **url_params):
        #return 'static handler _%s_' % args
        file_path = os.path.join(current_dir, 'themes', 'grid', 'static', *url_path)
        #raise Exception('%s' % (file_path,))
        return serve_file(file_path)

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root = Root()
    cherrypy.quickstart(root)