from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import urllib2

register_openers()

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
    return response_body