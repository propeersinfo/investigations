# -*- coding: utf-8 -*-

import Image

def is_pixel_white(pixel):
    if type(pixel) == int:
        raise Exception("pixel should be an int array - use colored images only")
    return pixel[0] == 255 and pixel[1] == 255 and pixel[2] == 255

def is_column_filled(img, column):
    for row in xrange(img.size[1]):
        pixel = img.getpixel((column, row))
        if not is_pixel_white(pixel):
            return True
    return False

def calc_glyph_paddings(img):
    def get_left_padding(img):
        img_width = img.size[0]
        cnt = 0
        for col in xrange(img_width):
            if is_column_filled(img, col):
                return cnt
            cnt += 1
        return img_width

    def get_right_padding(img):
        img_width = img.size[0]
        cnt = 0
        for col in reversed(xrange(img_width)):
            if is_column_filled(img, col):
                return cnt
            cnt += 1
        return img_width

    return get_left_padding(img), get_right_padding(img)

class Glyph():
    def __init__(self, image):
        if type(image) == str:
            self.image = Image.open(image)
        else:
            self.image = image
    def get_width(self):
        return self.image.size[0]
    def get_height(self):
        return self.image.size[1]
    def get_horiz_paddings(self):
        return calc_glyph_paddings(self.image)
    def crop(self, box):
        if not box:
            box = 0, 0, self.image.size[0], self.image.size[1]
        return Glyph(self.image.crop(box))
    def crop_horizontal(self, left, right):
        box = left, 0, right, self.image.size[1]
        return Glyph(self.image.crop(box))
    def crop_removing_at_left_and_right(self, left, right):
        box = (left, 0, self.image.size[0] - right, self.image.size[1])
        return self.crop(box)
    def show(self):
        return self.image.show()
    def break_into_glyphs(self):
        char_glyphs = []
        full_width = self.get_width()
        col = 0
        while col < full_width:
            # 1) skip non filled columns
            while col < full_width:
                if is_column_filled(self.image, col):
                    break
                col += 1

            char_start = col
            # 2) go till the first non filled column
            while col < full_width:
                if not is_column_filled(self.image, col):
                    break
                col += 1
            char_end = col
            if char_start == char_end:
                raise Exception("char_start == char_end")
            char_glyphs.append(self.crop_horizontal(char_start, char_end))
            #print char_start, char_end
        return char_glyphs
    def break_into_glyph_map(self, chars, map):
        glyphs = self.break_into_glyphs()
        if len(glyphs) > len(chars):
            raise Exception("%s > %s" % (len(glyphs), len(chars)))
        for i in xrange(len(glyphs)):
            map.set(chars[i], glyphs[i])
        return map

class GlyphMap():
    def __init__(self):
        self.map = {}
    def set(self, char, glyph):
        self.map[char.upper()] = glyph
        self.map[char.lower()] = glyph
    def get(self, char):
        return self.map.get(char)

"""
def get_glyph_by_char(glyhps_file, char):
    char = char.lower()
    img = Image.open(glyhps_file)
    if CHAR_TO_GLYPH.has_key(char):
        row, col = CHAR_TO_GLYPH[char]
        return get_glyph_by_position(img, row, col)
    return None
"""

"""
def render(text):
    def remove_extra_space(glyph):
        left, right = glyph.get_horiz_paddings()
        left = min(left, left-2)
        right = min(right, right-2)
        return glyph.crop_removing_at_left_and_right(left,right)
    new = Image.new("RGB", (800, CHAR_SIZE[1]))
    left = 0
    for ch in text:
        glyph = get_glyph_by_char('parcel1.png', ch)
        if glyph:
            glyph = remove_extra_space(glyph)
            print glyph
            new.paste(glyph.image, (left,0))
            left += glyph.get_width()
    new.show()
"""

COLOR_WHITE = (255, 255, 255)

class Renderer():
    def __init__(self, space_width):
        self.map2glyph = GlyphMap()
        space_glyph = Glyph(Image.new("RGB", (space_width,1), COLOR_WHITE))
        self.map2glyph.set(' ', space_glyph)
    def parse_glyphs_file(self, abc_file, chars):
        Glyph(abc_file).break_into_glyph_map(chars, self.map2glyph)
    def render(self, text):
        height = self.map2glyph.get('a').get_height()
        render = Image.new("RGB", (500,height), COLOR_WHITE)
        left = 0
        for char in text:
            glyph = self.map2glyph.get(char)
            if glyph:
                render.paste(glyph.image, (left,0))
                left += glyph.get_width()
                left += 3
        return render

renderer = Renderer(space_width=8)
renderer.parse_glyphs_file("a-z0-9_37pt.png",  u"abcdefghijklmnopqrstuvwxyz0123456789`_")
renderer.parse_glyphs_file("special_37pt.png", u"`~!@#№$%^&*()-_=+[]{}:;'\"<>,./\?__")
renderer.parse_glyphs_file("abc-cyr_37pt.png", u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя`_")
renderer.render(u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя`_").show()