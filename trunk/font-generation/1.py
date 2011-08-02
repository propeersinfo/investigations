import Image

CHAR_SIZE = (46,68)

CHAR_TO_GLYPH = {
    'a': (0,0),
    'b': (1,0),
    'c': (1,4)
}

def get_glyph_by_position(img, row, col):
    left = col * (CHAR_SIZE[0] + 1)
    top = row * (CHAR_SIZE[1] + 1)
    right = left + CHAR_SIZE[0]
    bottom = top + CHAR_SIZE[1]
    box = (left, top, right, bottom)
    #print "%d:%d:%d:%d" % box
    return img.crop(box)

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
    new = Image.new("RGB", (500, CHAR_SIZE[1]))
    left = 0
    for ch in text:
        crop = get_glyph_by_char('parcel1.png', ch)
        if crop:
            print new
            print crop
            new.paste(crop, (left,0))
            left += crop.size[0]
    new.show()

def calc_glyph_paddings(glyphs_file):
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

    img = get_glyph_by_char(glyphs_file, 'a')
    return get_left_padding(img), get_right_padding(img)

glyphs_file = "parcel1.png"
#extract_glyph_images(glyphs_file)
#render("aa bb")
calc_glyph_paddings(glyphs_file)