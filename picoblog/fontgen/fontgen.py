# -*- coding: utf-8 -*-

import os
import re
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from google.appengine.api import images
from models import FontRenderCache

import request
from fontgen.image import Image
from fontgen.renderer import Renderer

class RenderFontHandler(request.BlogRequestHandler):
    def get(self):
        #font_size = int(self.request.get("size")) # points
        font_size = 37

        #font_name = self.request.get("font")
        font_name = "parcel"

        text = self.request.get("text")
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)

        #text = u"`~!@#№$%^&*()- _ = + []{}:;'\" >< ,./\\?"
        #text = u"`~!@#№$%^&*()- _ = + []{}:;'\" >"
        #text = u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
        #text = u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
        
        #self.response.headers['Content-Type'] = "text/plain"
        #self.response.out.write("text: %s" % text)
        #return
        #raise Exception("text: %s" % text)

        cached = FontRenderCache.find(font_name, font_size, text)
        if cached:
            image_data = cached.render
            self.response.headers['Content-Type'] = "image/png"
            self.response.out.write(image_data)
        else:
            image = self.render(font_name, font_size, text)
            FontRenderCache.insert_new(font_name, font_size, text, image)
            self.response.headers['Content-Type'] = "image/png"
            image.save(self.response.out)

    def render(self, font_name, font_size, text):
        renderer = Renderer(char_gap=3, space_width=7)
        font_files = [
            [ "font-37pt-latin.png",  u"abcdefghijklmnopqrstuvwxyz0123456789`_" ],
            #[ "special_37pt.png", u"`~!@#№$\%^&*()-_=+[]{}:;'\"<>,./\\?__" ], # outdated
            [ "font-37pt-cyr.png", u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя`_" ],
            [ "font-37pt-special.png", u"`~!@#№$%^&*()- _ = + []{}:;'\" >< ,./\\?" ],
            [ 'font-37pt-typo.png', u'“”«»–—' ],
        ]
        for pair in font_files:
            file = pair[0]
            file = os.path.join(os.path.split(__file__)[0], file)
            #self.response.out.write("<xmp>Debug: %s\n" % os.path.exists(file))
            renderer.parse_glyphs_file(file, pair[1].replace(' ', ''))
        return renderer.render(text)


application = webapp.WSGIApplication(
        [
         ('/font.*', RenderFontHandler),
         ],

        debug=True)

def main():
    util.run_wsgi_app(application)

if __name__ == "__main__":
    main()
