# -*- coding: utf-8 -*-

import unicodedata

import Image

PIXEL_PRESENCE_THRESHOLD = 253.0
COLOR_WHITE = (255, 255, 255)

def unicode_to_latin(unicode):
    return unicodedata.normalize('NFKD', unicode).encode('ascii', 'ignore').lower()

def get_pixel_brightness(pixel):
    if type(pixel) == int:
        raise Exception("pixel should be an int array - use full color images")
    return float(pixel[0] + pixel[1] + pixel[2]) / 3.0

def get_column_brightness(img, column):
    num_pixels = img.size[1]
    sum_brightness = 0.0
    for row in xrange(num_pixels):
        pixel = img.getpixel((column, row))
        sum_brightness += get_pixel_brightness(pixel)
    return sum_brightness / num_pixels

def is_column_filled(img, column):
    return get_column_brightness(img, column) < 255.0

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
        #if len(glyphs) > len(chars):
        #    raise Exception("%s > %s" % (len(glyphs), len(chars)))
        count = min(len(glyphs), len(chars))
        for i in xrange(count):
            map.set(chars[i], glyphs[i])
        return map
    def get_blind_pixels_info(self):
        blind_left = get_column_brightness(self.image, 0) > PIXEL_PRESENCE_THRESHOLD
        blind_right = get_column_brightness(self.image, self.get_width() - 1) > PIXEL_PRESENCE_THRESHOLD
        return 1 if blind_left else 0, 1 if blind_right else 0

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

class Renderer():
    def __init__(self, char_gap, space_width):
        self.char_gap = char_gap
        self.map2glyph = GlyphMap()
        space_glyph = Glyph(Image.new("RGB", (space_width,1), COLOR_WHITE))
        self.map2glyph.set(' ', space_glyph)
    def parse_glyphs_file(self, abc_file, chars):
        Glyph(abc_file).break_into_glyph_map(chars, self.map2glyph)
    def render(self, text):
        height = self.map2glyph.map.values()[0].get_height() # get any glyph to calculate image's height
        render = Image.new("RGB", (600,height), COLOR_WHITE)
        left = 0
        print "text's length: %d" % len(text)
        for char in text:
            glyph = self.find_glyph(char)
            if glyph:
                blind_left, blind_right = glyph.get_blind_pixels_info()
                if blind_left or blind_right:
                    print "blind pixels detected: %s %s" % (blind_left, blind_right)
                render.paste(glyph.image, (left,0))
                left += glyph.get_width()
                left += self.char_gap
                #left -= blind_left + blind_right
                #left += int(11.00000)
            else:
                print "a glyph is missed for ord:%s" % ord(char)
        return render
    def find_glyph(self, original_char):
        # find glyph by a character
        # if not found try to convert the character to latin-1 then
        for char in (original_char, unicode_to_latin(original_char)):
            glyph = self.map2glyph.get(char)
            if glyph: return glyph
        return None

renderer = Renderer(char_gap=3, space_width=8)
font_files = [
    [ "a-z0-9_37pt.png",  u"abcdefghijklmnopqrstuvwxyz0123456789`_" ],
    [ "special_37pt.png", u"`~!@#№$\%^&*()-_=+[]{}:;'\"<>,./\?__" ],
    [ "abc-cyr_37pt.png", u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя`_" ]
]
for pair in font_files:
    renderer.parse_glyphs_file(pair[0], pair[1])
#renderer.parse_glyphs_file("a-z0-9_37pt.png",  u"abcdefghijklmnopqrstuvwxyz0123456789`_")
#renderer.parse_glyphs_file("special_37pt.png", u"`~!@#№$%^&*()-_=+[]{}:;'\"<>,./\?__")
#renderer.parse_glyphs_file("abc-cyr_37pt.png", u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя`_")

#renderer.render(font_files[0][1]).show()
#renderer.render(u"Ludvikovsky & Garanian 1971").show()
#renderer.render(u"Alexander Gradsky / А. Градский 1971-74").show()


unicode = u"Romualdas Grabštas Ensemble 197x"
#print unicodedata.normalize('NFKD', unicode).encode('ascii', 'ignore').lower()
renderer.render(unicode).show()
