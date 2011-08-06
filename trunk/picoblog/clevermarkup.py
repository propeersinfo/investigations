import cgi
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

#class MarkupTagImage():
#    regex = '\[([^\]]+\.(jpg|jpeg|png|gif))\]'
#    replacement = '<img src="\1" width="140" alt="\1">'
#    @classmethod
#    def replace_in_markup(cls, markup_text):
#        return re.sub(cls.regex, cls.replacement, markup_text)
#    @classmethod
#    def is_presented_in_markup(cls, markup_text):
#        modified = cls.replace_in_markup(markup_text)
#        return modified != markup_text

def handle_custom_tag_image(text):
    regex = re.compile("\[([^\]]+jpg)\]", re.IGNORECASE)
    replacement = '<img src="http://dl.dropbox.com/u/%s/sg/\\1" width="140" alt="\\1">' % defs.DROPBOX_USER
    return regex.sub(replacement, text)

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
    html = markup_text
    if recognize_links or rich_markup:
        html = handle_custom_tag_http_link(html)
    if rich_markup:
        html = handle_custom_tag_image(html)
        html = handle_custom_tag_mp3(html)
        html = handle_custom_tag_playlist(html)
        html = handle_custom_tag_youtube(html)
        html = handle_custom_tag_mixcloud(html)
    html = html.replace('\n', '<br>\n') # NB: the last transformation
    return html

class Paragraph():
    def __init__(self, name, body):
        self.name = name
        self.body = body
    @classmethod
    def parse(cls, input):
        m = re.search('#\s*(\w+)\s*([\r\n].*)', input, re.MULTILINE|re.DOTALL)
        if m:
            return Paragraph(m.group(1).strip(), m.group(2).strip())
        else:
            return Paragraph(None, input)

class ParagraphCollection(list):
    def __init__(self, p_list = list()):
        list.__init__(self)
        self.hash = {}
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
            if p.name and names_wanted.count(p.name) > 0:
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

    double_break = re.compile(r'\n\n', re.MULTILINE|re.DOTALL)
    pp = double_break.split(s)                # break into paragraphs
    pp = map(lambda str: str.strip(), pp)     # strip each paragraph
    pp = filter(lambda str: len(str) > 0, pp) # skip empty paragraphs
    pp = map(lambda str: Paragraph.parse(str), pp)
    return ParagraphCollection(pp)

class SimpleMarkup():
    def __init__(self, for_comment, rich_markup = True, recognize_links = True):
        self.for_comment = for_comment
        self.rich_markup = rich_markup
        self.recognize_links = recognize_links
    def generate_html(self, markup_text):
        paragraphs = break_into_paragraphs(markup_text)
        #assert type(paragraphs[0]) == Paragraph
        result_string = ''
        for p in paragraphs:
            result_string += "<p>%s</p>\n" % markup2html_paragraph(p.body)
        return result_string

class CleverMarkup(SimpleMarkup):
    RECOGNIZED_PARAGRAPH_NAMES = ['picture', 'tracklist', 'techinfo', 'download']
    article_id = None
    class CleverMarkupFailedToMatchInput(Exception):
        pass
    def __init__(self, for_comment, rich_markup = True, recognize_links = True):
        SimpleMarkup.__init__(self, for_comment, rich_markup, recognize_links)
    def generate_html(self, markup_text):
        #raise Exception("markup_text for %s is %s" % (self.article_id, markup_text))
        if self.for_comment:
            return SimpleMarkup.generate_html(self, markup_text)
        pp = break_into_paragraphs(markup_text)
        #raise Exception("pp: %s" % [p.body for p in pp])
        result_string = ''
        before, named, after = pp.break_into_three_groups(self.RECOGNIZED_PARAGRAPH_NAMES)
        #raise Exception("named: %s" % [p.body for p in named]) # ok
        def para2html(paragraph):
            return markup2html_paragraph(paragraph.body)
        rv = {
            'before': map(para2html, before),
            'middle': self.get_the_middle(pp),
            'after':  map(para2html, after)
        }
        #raise Exception('rv: %s' % rv)
        return rv
    def get_the_middle(self, pp):
        #raise Exception("get_the_middle begin: %s" % [p.body for p in pp]) # still okay
        def break_tracklist_into_sides(text):
            #divider = re.compile('B\d\.?\s', re.MULTILINE|re.IGNORECASE)
            #res = re.split(divider, text, 1)
            m = re.search('^(.*)(B0?1\.?\s.*)$', text, re.MULTILINE|re.IGNORECASE|re.DOTALL)
            if m:
                return markup2html_paragraph(m.group(1).strip()),\
                       markup2html_paragraph(m.group(2).strip())
            else:
                return None, None
        hash = {}

        msg1 = 'list items: %s' % [p.body for p in pp]
        msg2 = 'hash items: %s' % [p.body for p in pp.hash.values()]
        #raise Exception('\nmsg1: %s\nmsg2: %s' % (msg1, msg2))

        #msg1 = "pp before loop: %s" % [p.body for p in pp]
        #msg2 = "picture: %s" % pp.get_named_paragraph('picture').body
        #if True: raise Exception("\n%s\n%s" % (msg1, msg2))
        pp_id_1 = id(pp)
        for name in self.RECOGNIZED_PARAGRAPH_NAMES:
            p = pp.get_named_paragraph(name)
            pp_id_2 = id(pp)
            #raise Exception("%s vs %s" % (pp_id_1, pp_id_2))
            #if True: raise Exception("p = %s" % p.body) # WRONG!
            if p:
                if name == 'tracklist':
                    side_a, side_b = break_tracklist_into_sides(p.body)
                    if side_a and side_b:
                        hash[name] = {
                            'side_a' : side_a,
                            'side_b' : side_b
                        }
                        continue
                hash[name] = markup2html_paragraph(p.body if p else 'no-named-p-%s' % name)
        #if True: raise Exception("get_the_middle end: %s / article:%s" % (hash, self.article_id)) # wrong here!
        return hash if len(hash) > 0 else None
        #raise Exception(len(hash))
        #return None

# main function
def markup2html(markup_text, for_comment, rich_markup = True, recognize_links = True, article_id = None):
    #return SimpleMarkup(rich_markup, recognize_links).generate_html(markup_text)
    markup = CleverMarkup(for_comment, rich_markup, recognize_links)
    markup.article_id = article_id
    return markup.generate_html(markup_text)

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
        CleverMarkup(for_comment=False).generate_html(
            "000\n\n"
            "111\n\n"
            "# picture\n"
            "[222.jpg]\n\n"
            "33\n\n"
            "# download\n"
            "Download: rapidshare.com 127 MB\n"
            "Download: continued\n\n"
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
    #unittest.main()
    #TestCleverMarkup().test_some()
    s = ',, [saarsalu-1980.jpg] ,, [111.mp3]'
    s = handle_custom_tag_image(s)
    s = handle_custom_tag_mp3(s)
    print s