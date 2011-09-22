import sys
import urllib2

from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
from BeautifulSoup import BeautifulSoup

register_openers()

class OnlineImageInfo():
    def __init__(self, thumbnail_image, full_image, full_page = None):
        self.thumbnail_image = thumbnail_image
        self.full_image = full_image
        self.full_page = full_page
    def get_thumbnail_image_url(self):
        return self.thumbnail_image
    def get_full_image_url(self):
        return self.full_image
    def get_full_page_url(self):
        return self.full_page

def upload_image_fastpic(file_name, open_binary = True):
    fd = open(file_name, "rb" if open_binary else "r")
    post_data, headers = multipart_encode({
            "file1": fd,
            "method": "file",
            "check_thumb": "size",
            "uploading": "1",
            "orig_rotate": "0",
            "thumb_size" : "200"
    })
    post_url = "http://fastpic.ru/upload?api=1"
    request = urllib2.Request(post_url, post_data, headers)
    response = urllib2.urlopen(request)
    response_body = response.read()
    #print "response's info: %s" % response.info()
    #response_body = open("fastpic.xml").read()
    xml = BeautifulSoup(response_body)
    status = xml.uploadsettings.status.string
    error = xml.uploadsettings.error.string
    if error:
        raise RuntimeError("cannot upload image %s because: %s" % (file_name, error))
    #thumbpath = xml.uploadsettings.thumbpath.string
    #imagepath = xml.uploadsettings.imagepath.string
    viewurl = xml.uploadsettings.viewurl.string
    viewfullurl = xml.uploadsettings.viewfullurl.string
    return OnlineImageInfo(thumbnail_image=xml.uploadsettings.thumbpath.string,
                           full_image=xml.uploadsettings.imagepath.string,
                           full_page=viewurl)

if __name__ == '__main__':
    img = upload_image_fastpic(sys.argv[1])
    print img.get_full_image_url()

#def upload_image(image_file):
#    image_file = os.path.abspath(image_file)
#    link_file = '%s.imagelink' % image_file
#    cwd = os.getcwd()
#    uploader_dir = "C:\\Portable\\zenden-image-uploader"
#    upload_cmd = ['imgupload.exe', '--server', 'fastpic.ru', '--codelang', 'bbcode', '--codetype', 'Images', image_file]
#    try:
#        print "uploading image '%s'" % image_file
#        os.chdir(uploader_dir)
#        #p = subprocess.Popen(upload_cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#        #(bbcode, err) = p.communicate()
#        #print "out: %s" % out
#        #print 'err: %s' % err
#        bbcode = "http://faspic.ru/qwertyuiop"
#        rewrite_file(link_file, bbcode)
#    finally:
#        os.chdir(cwd)