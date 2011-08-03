# -*- coding: utf-8 -*-

import os
import sys
import cgi
import logging
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from google.appengine.api import images

import request
from fontgen.image import Image
from fontgen.renderer import Renderer

class RenderFontHandler(request.BlogRequestHandler):
    def get(self):
        text = self.request.get("text")

        renderer = Renderer(char_gap=3, space_width=7)
        font_files = [
            [ "font-37pt-latin.png",  u"abcdefghijklmnopqrstuvwxyz0123456789`_" ],
            #[ "special_37pt.png", u"`~!@#№$\%^&*()-_=+[]{}:;'\"<>,./\\?__" ], # outdated
            [ "font-37pt-cyr.png", u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя`_" ],
            [ "font-37pt-special.png", u"`~!@#№$%^&*()- _ = + []{}:;'\" >< ,./\\?" ],
        ]
        for pair in font_files:
            file = pair[0]
            file = os.path.join(os.path.split(__file__)[0], file)
            #self.response.out.write("<xmp>Debug: %s\n" % os.path.exists(file))
            renderer.parse_glyphs_file(file, pair[1].replace(' ', ''))

        #img = Image.new(None, (200,200), (255,25,255))
        img = renderer.render(text)
        self.response.headers['Content-Type'] = "image/png"
        img.save(self.response.out)



application = webapp.WSGIApplication(
        [
         ('/font.*', RenderFontHandler),
         ],

        debug=True)

def main():
    util.run_wsgi_app(application)

if __name__ == "__main__":
    main()
