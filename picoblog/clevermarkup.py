import sys
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

class MarkupTagImage():
    regex = '\[([^\]]+\.(jpg|jpeg|png|gif))\]'
    replacement = '<img src="\1">'
    @classmethod
    def replace_in_markup(cls, markup_text):
        return re.sub(cls.regex, cls.replacement, markup_text)
    @classmethod
    def is_presented_in_markup(cls, markup_text):
        modified = cls.replace_in_markup(markup_text)
        return modified != markup_text

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

def markup2html_paragraph(markup_text, rich_markup = True, recognize_links = True):
    html = markup_text.replace('\n', '<br>\n')
    if recognize_links or rich_markup:
        html = handle_custom_tag_http_link(html)
    if rich_markup:
        html = handle_custom_tag_mp3(html)
        html = handle_custom_tag_playlist(html)
        html = handle_custom_tag_youtube(html)
        html = handle_custom_tag_mixcloud(html)
    return html

class Paragraph():
    def __init__(self, name, body):
        self.name = name
        self.body = body
    @classmethod
    def parse(cls, input):
        m = re.search(r'^#\s*(\w+)\s*([\r\n].*)$', input)
        if m:
            return Paragraph(m.group(1).strip(), m.group(2).strip())
        else:
            return Paragraph(None, input)

class ParagraphCollection(list):
    hash = {}
    def __init__(self, p_list = []):
        list.__init__(self)
        for p in p_list:
            self.append(p)
            if p.name:
                self.hash[p.name.lower()] = p
    def get_named_paragraph(self, name):
        return self.hash.get(name.lower())
    def break_into_three_groups(self, names_wanted):
        before = ParagraphCollection()
        named = ParagraphCollection()
        after = ParagraphCollection()
        where_to_add_to = before
        for idx, p in enumerate(self):
            if p.name and names_wanted.index(p.name) >= 0:
                named.append(p)
                where_to_add_to = after
            else:
                where_to_add_to.append(p)
        return before, named, after

def break_into_paragraphs(markup_text):
    def convert_line_ends_to_unix_type(str):
        return str.replace('\r\n', '\n').replace('\r', '\n')
    s = markup_text
    s = convert_line_ends_to_unix_type(s)

    double_break = re.compile(r'\n\n')
    pp = double_break.split(s)                # break into paragraphs
    pp = map(lambda str: str.strip(), pp)     # strip each paragraph
    pp = filter(lambda str: len(str) > 0, pp) # skip empty paragraphs
    pp = map(lambda str: Paragraph.parse(str), pp)
    return ParagraphCollection(pp)

class SimpleMarkup():
    def __init__(self, rich_markup = True, recognize_links = True):
        self.rich_markup = rich_markup
        self.recognize_links = recognize_links
    def generate_html(self, markup_text):
        paragraphs = break_into_paragraphs(markup_text)
        assert type(paragraphs[0]) == Paragraph
        result_string = ''
        for p in paragraphs:
            result_string += "<p>%s</p>\n" % markup2html_paragraph(p)
        return result_string

class CleverMarkup(SimpleMarkup):
    class CleverMarkupFailedToMatchInput(Exception):
        pass
    def __init__(self, rich_markup = True, recognize_links = True):
        SimpleMarkup.__init__(self, rich_markup, recognize_links)
    def generate_html(self, markup_text):
        pp = break_into_paragraphs(markup_text)
        print "picture:", pp.get_named_paragraph("picture")
        print "tracklist:", pp.get_named_paragraph("tracklist")
        print "techinfo:", pp.get_named_paragraph("techinfo")
        print "download:", pp.get_named_paragraph("download")
        result_string = ''
        for p in pp:
            result_string += "<p>%s</p>\n" % p.body
        before, named, after = pp.break_into_three_groups(['picture', 'tracklist', 'techinfo', 'download'])
        print len(before)
        print len(named)
        print len(after)
        return result_string
#    def find_image_paragraphs(self, paragraphs):
#        indices = []
#        for idx, p in enumerate(paragraphs):
#            if MarkupTagImage.is_presented_in_markup(p):
#                indices.append(idx)
#        return indices
#    def find_download_paragraphs(self, paragraphs):
#        def is_dl_presented(text):
#            return re.search(r'(rapidshare\.com|narod\.ru)', text)
#        indices = []
#        for idx, p in enumerate(paragraphs):
#            if is_dl_presented(p):
#                indices.append(idx)
#        return indices

# main function
def markup2html(markup_text, rich_markup = True, recognize_links = True):
    #return SimpleMarkup(rich_markup, recognize_links).generate_html(markup_text)
    return CleverMarkup(rich_markup, recognize_links).generate_html(markup_text)

############## tests

class TestBreakIntoParagraphs(unittest.TestCase):
    def test_break_into_paragraphs(self):
        self.assertEqual(["111"], break_into_paragraphs("111"))
        self.assertEqual(["111"], break_into_paragraphs("111\n"))
        self.assertEqual(["111"], break_into_paragraphs("\n111"))
        self.assertEqual(["111","222"], break_into_paragraphs("111\r\n\r\n222")) # windows
        self.assertEqual(["111","222"], break_into_paragraphs("111\r\r222"))     # mac os
        self.assertEqual(["111","222"], break_into_paragraphs("111\n\n222"))     # unix
        self.assertEqual(["111","222"], break_into_paragraphs("111\n\n\n\n\n\n\n\n222"))

class TestSimpleMarkup(unittest.TestCase):
    def html(self, markup):
        return SimpleMarkup().generate_html(markup)
    def test_no_line_breaks(self):
        self.assertEqual("<p>111</p>\n", self.html("111"))
    def test_one_line_break(self):
        self.assertEqual("<p>111<br>\n222</p>\n", self.html("111\n222"))
    def test_two_line_breaks(self):
        self.assertEqual("<p>111</p>\n<p>222</p>\n", self.html("111\n\n222"))
    def test_three_line_breaks(self):
        self.assertEqual("<p>111</p>\n<p>222</p>\n", self.html("111\n\n\n222"))

class TestCleverMarkup(unittest.TestCase):
    def test_some(self):
        CleverMarkup().generate_html(
            "000\n\n"
            "111\n\n"
            "# picture\n"
            "[222.jpg]\n\n"
            "33\n\n"
            "# download\n"
            "Download: rapidshare.com 127 MB\n\n"
            "end1\n\n"
            "end1\n\n"
        )

class TestMarkupTagImage(unittest.TestCase):
    def test_all(self):
        self.assertTrue(MarkupTagImage.is_presented_in_markup("[111.jpg]"))
        self.assertTrue(MarkupTagImage.is_presented_in_markup("[111.jpeg]"))
        self.assertTrue(MarkupTagImage.is_presented_in_markup("[111.png]"))
        self.assertTrue(MarkupTagImage.is_presented_in_markup("[111.gif]"))
        self.assertFalse(MarkupTagImage.is_presented_in_markup("[111jpg]"))

if __name__ == '__main__':
    unittest.main()
    #TestCleverMarkup().test_some()