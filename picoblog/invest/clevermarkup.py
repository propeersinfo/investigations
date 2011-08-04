import re
import unittest

import defs

"""
Simple markup support.
Each new line character becomes a <br>.
HTTP links becomes <a> tags automatically.
HTML is allowed.
Custom []-styled tags are supported:
- [some.mp3]
- [http://youtube.com/...]
- [http://mixcloud.com/...]
"""

# [http://ya.ru/]
def handle_custom_tag_http_link(input):
    for regex_and_replace in [
                [ r'^(http://[^\s]+)',    '<a href="\\1">\\1</a>'    ], # a link at the most beginning
                [ r'(\s)(http://[^\s]+)', '\\1<a href="\\2">\\2</a>' ]  # all other cases
    ]:
        regex = regex_and_replace[0]
        replace = regex_and_replace[1]
        input = re.sub(regex, replace, input)
    return input

# [http://www.youtube.com/watch?v=XXXXXXXXX]
def handle_custom_tag_youtube(input):
    regex = "\[\s*(http://)?(www\.)?youtube\.com/watch\?v=([a-zA-Z0-9-_]+)\s*\]"
    replace =\
      '<a href="http://www.youtube.com/watch?v=\\3">'\
      '<img class="youtube" ytid="\\3" src="http://img.youtube.com/vi/\\3/0.jpg" width="480" height="360">'\
      '</a>'\
      ''
      #'<noscript>'\
      #'<iframe src="http://www.youtube.com/embed/\\3?autoplay=1&theme=dark" width="480" height="360" frameborder="0" allowfullscreen="1"></iframe>'\
      #'</noscript>'\
    return re.sub(regex, replace, input)

# [dir/cool track.mp3]
def handle_custom_tag_mp3(input):
    regex = "\[([^\]]+mp3)\]"
    repl_link  = "http://dl.dropbox.com/u/%s/sg/\\1" % defs.DROPBOX_USER
    repl_swf   = "http://dl.dropbox.com/u/%s/dewplayer-mini.swf" % defs.DROPBOX_USER
    repl_flash = "<object width='160' height='18'><embed src='" + repl_swf + "' width='160' height='18' type='application/x-shockwave-flash' flashvars='&mp3=" + repl_link + "' quality='high'></embed></object>"
    repl_dload = "<a href=\"%s\">\\1</a>" % repl_link
    repl = "%s %s" % (repl_flash, repl_dload)

    return re.sub(regex, repl, input)

# [http://www.mixcloud.com/user/mixname/]
def handle_custom_tag_mixcloud(input):
    regex = "\[\s*(http://)?(www.)?mixcloud.com/([a-zA-Z0-9-]+)/([a-zA-Z0-9-]+)/?\s*\]"
    replace  = '<object height="400" width="400"><param name="movie" value="http://www.mixcloud.com/media/swf/player/mixcloudLoader.swf?feed=http%3A%2F%2Fwww.mixcloud.com%2F\\3%2F\\4%2F&amp;embed_uuid=3b4627b1-74e1-43ef-bc52-717acca644d4&amp;embed_type=widget_standard"><param name="allowFullScreen" value="true"><param name="allowscriptaccess" value="always"><embed src="http://www.mixcloud.com/media/swf/player/mixcloudLoader.swf?feed=http%3A%2F%2Fwww.mixcloud.com%2F\\3%2F\\4%2F&amp;embed_uuid=3b4627b1-74e1-43ef-bc52-717acca644d4&amp;embed_type=widget_standard" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true" height="400" width="400"></object>'
    return re.sub(regex, replace, input)

# [3x3.playlist]
def handle_custom_tag_playlist(input):
    regex = '\[([^\]]+playlist)\]'
    replace = '<object width="240" height="200">'\
              '<embed src="http://dl.dropbox.com/u/%s/dewplayer-playlist.swf" '\
              'width="240" height="200" '\
              'type="application/x-shockwave-flash" '\
              'flashvars="&xml=http://dl.dropbox.com/u/%s/sg/\\1&autoreplay=1" quality="high">'\
              '</embed></object>' % (defs.DROPBOX_USER, defs.DROPBOX_USER)
    return re.sub(regex, replace, input)

# main function
#def markup2html(markup_text, rich_markup = True, recognize_links = True):
#    html = markup_text.replace('\n', '<br>\n')
#    if recognize_links or rich_markup:
#        html = handle_custom_tag_http_link(html)
#    if rich_markup:
#        html = handle_custom_tag_mp3(html)
#        html = handle_custom_tag_playlist(html)
#        html = handle_custom_tag_youtube(html)
#        html = handle_custom_tag_mixcloud(html)
#    return html

def handle_paragraph(markup_text, rich_markup = True, recognize_links = True):
    html = markup_text.replace('\n', '<br>\n')
    if recognize_links or rich_markup:
        html = handle_custom_tag_http_link(html)
    if rich_markup:
        html = handle_custom_tag_mp3(html)
        html = handle_custom_tag_playlist(html)
        html = handle_custom_tag_youtube(html)
        html = handle_custom_tag_mixcloud(html)
    return html

def break_into_paragraphs(markup_text):
    def convert_line_ends_to_unix_type(str):
        return str.replace('\r\n', '\n').replace('\r', '\n')
    s = markup_text
    #print "s: %s" % [ ord(ch) for ch in s]
    s = convert_line_ends_to_unix_type(s)
    #print "s: %s" % [ ord(ch) for ch in s]

    double_break = re.compile(r'\n\n')
    pp = double_break.split(s)                # break into paragraphs
    pp = map(lambda str: str.strip(), pp)     # strip each paragraph
    pp = filter(lambda str: len(str) > 0, pp) # skip empty paragraphs
    return pp

# main function
def markup2html(markup_text, rich_markup = True, recognize_links = True):
    paragraphs = break_into_paragraphs(markup_text)

    result_string = ''
    for p in paragraphs:
        p_html = handle_paragraph(p)
        result_string += "<p>%s</p>\n" % p_html
    return result_string

class TestTransformations(unittest.TestCase):
    def setUp(self):
        pass
    def test_break_into_paragraphs(self):
        self.assertEqual(["111"], break_into_paragraphs("111"))
        self.assertEqual(["111"], break_into_paragraphs("111\n"))
        self.assertEqual(["111"], break_into_paragraphs("\n111"))
        self.assertEqual(["111","222"], break_into_paragraphs("111\r\n\r\n222")) # windows
        self.assertEqual(["111","222"], break_into_paragraphs("111\r\r222"))     # mac os
        self.assertEqual(["111","222"], break_into_paragraphs("111\n\n222"))     # unix
        self.assertEqual(["111","222"], break_into_paragraphs("111\n\n\n\n\n\n\n\n222"))
    def test_no_line_breaks(self):
        self.assertEqual("<p>111</p>\n", markup2html("111"))
    def test_one_line_break(self):
        self.assertEqual("<p>111<br>\n222</p>\n", markup2html("111\n222"))
    def test_two_line_breaks(self):
        self.assertEqual("<p>111</p>\n<p>222</p>\n", markup2html("111\n\n222"))
    def test_three_line_breaks(self):
        self.assertEqual("<p>111</p>\n<p>222</p>\n", markup2html("111\n\n\n222"))

if __name__ == '__main__':
    unittest.main()