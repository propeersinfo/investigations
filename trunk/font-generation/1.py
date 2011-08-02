import Image

CHAR_SIZE = (46,68)

# zero based
CHAR_TO_GLYPH = {
'a': (0,0),
'b': (1,0),
'c': (1,4),
'd' : (1,10),
'e' : (2,4),
'f' : (3,5),
'g' : (3,7),
'h' : (4,0),
'i' : (4,8),
'j' : (5,9),
'k' : (5,11),
'l' : (6,2),
'm' : (6,10),
'n' : (6,14),
'o' : (7,10),
'p' : (8,11),
'q' : (8, 14),
'r' : (9,0),
's' : (9,9),
't' : (10,2),
'u' : (10,10),
'v' : (11,14),
'w' : (12,2),
'x' : (12,4),
'y' : (12,5),
'z' : (12,10)
}

class Glyph():
    def __init__(self, image):
        self.image = image
    def get_width(self):
        return self.image.size[0]
    def get_horiz_paddings(self):
        return calc_glyph_paddings(self.image)
    def crop(self, box):
        if not box:
            box = 0, 0, self.image.size[0], self.image.size[1]
        return Glyph(self.image.crop(box))
    def crop_removing_at_left_and_right(self, left, right):
        box = (left, 0, self.image.size[0] - right, self.image.size[1])
        return self.crop(box)
    def show(self):
        return self.image.show()

def get_glyph_by_position(img, row, col):
    left = col * (CHAR_SIZE[0] + 1)
    top = row * (CHAR_SIZE[1] + 1)
    right = left + CHAR_SIZE[0]
    bottom = top + CHAR_SIZE[1]
    box = (left, top, right, bottom)
    #print "%d:%d:%d:%d" % box
    return Glyph(img.crop(box))

def extract_glyph_images(glyhps_file):
    MAX_GLYPHS_X = 15
    MAX_GLYPHS_Y = 5

    img = Image.open(glyhps_file)
    print "big image: %s:%s" % img.size
    for row in xrange(MAX_GLYPHS_Y):
        for col in xrange(MAX_GLYPHS_X):
            crop = get_glyph_by_position(img, row, col)
            new = Image.new("RGB", crop.size)
            new.paste(crop, (0,0))
            char_file = "glyphs/%02d_%02d.png" % (row+1, col+1)
            new.save(char_file, "PNG")
        print ""

def get_glyph_by_char(glyhps_file, char):
    char = char.lower()
    img = Image.open(glyhps_file)
    if CHAR_TO_GLYPH.has_key(char):
        row, col = CHAR_TO_GLYPH[char]
        return get_glyph_by_position(img, row, col)
    return None

def render(text):
    def remove_extra_space(glyph):
        left, right = glyph.get_horiz_paddings()
        left = min(left, left-3)
        right = min(right, right-3)
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

def calc_glyph_paddings(img):
    def is_pixel_white(pixel):
        return pixel[0] == 255 and pixel[1] == 255 and pixel[2] == 255

    def is_column_filled(img, column):
        for row in xrange(img.size[1]):
            pixel = img.getpixel((column, row))
            if not is_pixel_white(pixel):
                return True
        return False

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

glyphs_file = "parcel1.png"

#extract_glyph_images(glyphs_file)
render("abcdefghijklmnopqrstuvwxyz")

#calc_glyph_paddings(get_glyph_by_char(glyphs_file, 'a'))

#glyph = get_glyph_by_char(glyphs_file, 'b').crop((0,0,10,10))
#glyph = get_glyph_by_char(glyphs_file, 'b').crop_removing_at_left_and_right(3, 3)
#glyph.show()