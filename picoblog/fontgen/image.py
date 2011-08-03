import os
import subprocess

import png

class Image():
    source = None
    def __init__(self, size, meta, pixel_data):
        self.size = size
        self.meta = meta
        self.pixel_data = pixel_data
        #assert size[1] != 1
    def get_height(self):
        return self.size[1]
    def get_width(self):
        return self.size[0]
    def setpixel(self, pixel, point):
        x, y = point
        #print "y: %s" % y
        #print "source: %s" % self.source
        #print "dim: ", self.size
        row = self.pixel_data[y]
        start = x * self.meta['planes']
        row[start+0] = pixel[0]
        row[start+1] = pixel[1]
        row[start+2] = pixel[2]
    def getpixel(self, point):
        x, y = point
        row = self.pixel_data[y]
        start = x * self.meta['planes']
        return row[start + 0], row[start + 1], row[start + 2]
    @classmethod
    def new(cls, type, size, color):
        meta = { 'size': size, 'bitdepth': 8, 'planes': 3, 'greyscale': False, 'alpha': False }
        pixel_data = []
        for row in xrange(size[1]):
            row_data = list()
            for col in xrange(size[0]):
                row_data.append(color[0])
                row_data.append(color[1])
                row_data.append(color[2])
                #row_data.append(color[3])
            pixel_data.append(row_data)
        return Image(size, meta, pixel_data)
    @classmethod
    def open(cls, file):
        f = open(file, 'rb')
        img = png.Reader(f).read()
        meta = img[3]
        size = meta['size']
        assert meta['bitdepth'] == 8
        print 'planes:', meta['planes']
        assert meta['planes'] == 3
        assert meta['greyscale'] == False
        assert meta['alpha'] == False
        img = Image(size=size, meta=meta, pixel_data=list(img[2]))
        img.source = file
        return img
    def save(self, out):
        close = False
        if type(out) == str:
            out = open(out, 'wb')      # binary mode is important
            close = True
        w = png.Writer(self.get_width(),
                       self.get_height(),
                       greyscale=self.meta['greyscale'],
                       bitdepth=self.meta['bitdepth'],
                       planes=self.meta['planes'],
                       alpha=self.meta['alpha'])
        w.write(out, self.pixel_data)
        if close: out.close()
    def show(self):
        file = "C:\\Temp\\pypng.png"
        self.save(file)
        #os.system('"C:/Program Files/XnVew/XnView.exe"')
        subprocess.call(['C:\\Program Files\\XnView\\xnview.exe', file])
    def crop(self, box):
        left, top, right, bottom = box
        result_rows = []
        for row in xrange(top, bottom):
            result_row = []
            for col in xrange(left, right):
                px = self.getpixel((col, row))
                result_row.append(px[0])
                result_row.append(px[1])
                result_row.append(px[2])
                #result_row.append(px[3])
            result_rows.append(result_row)
        size = (right-left, bottom-top)
        meta = self.meta.copy()
        return Image(size, meta=meta, pixel_data=result_rows)
    def paste(self, image2, offset):
        for row in xrange(image2.get_height()):
            for col in xrange(image2.get_width()):
                px = image2.getpixel((col, row))
                self.setpixel(px, (col+offset[0], row+offset[1]))

if __name__ == "__main__":
    #img = Image.open('special_37pt.png')
    img = Image.open('font-37pt-latin.png')
    print img
    print img.getpixel((0,0))
    #img.save('out.png')
    cropped = img.crop((0,0,40,35))
    print cropped
    #cropped.show()
    #img.show()

    new = Image.new(None, (200,200), (255,255,255))
    new.paste(cropped, (0,0))
    new.show()