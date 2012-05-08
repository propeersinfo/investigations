import re
import unittest
import urllib2

import defs
import my_tags
import utils

"""
Simple markup support.
Each new line character becomes a <br>.
Two new lines -> new paragraph.
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

CUSTOM_TAG_IMAGE = re.compile("\[([^\]]+(jpe?g|png|gif))\]", re.IGNORECASE)

def handle_custom_tag_image(text):
    #replacement = '<img src="http://dl.dropbox.com/u/%s/sg/\\1" alt="\\1">' % defs.DROPBOX_USER
    #replacement = '<img src="/static/cover.jpg" width="140" alt="\\1">'
    #return regex.sub(replacement, text)
    def replacer(m):
      addr = m.group(1)
      if addr.startswith('http'):
        return '<img src="%s">' % addr
      else:
        return '<img src="http://dl.dropbox.com/u/%s/sg/%s" alt="%s">' % (defs.DROPBOX_USER, addr, addr)
    if defs.SHOW_REAL_IMAGES:
        return re.sub(CUSTOM_TAG_IMAGE, replacer, text)
    else:
        return re.sub(CUSTOM_TAG_IMAGE, '<img src="/static/cover.jpg">', text)

LINK_1 = re.compile('^(https?://[^\s]+)', re.IGNORECASE)    # a link at the most beginning
LINK_2 = re.compile('(\s)(https?://[^\s]+)', re.IGNORECASE) # all other cases

# http://ya.ru/
def handle_custom_tag_http_link(input):
    for regex_and_replace in [
                [LINK_1, '<a href="\\1">\\1</a>'    ],
                [LINK_2, '\\1<a href="\\2">\\2</a>' ]
    ]:
        regex = regex_and_replace[0]
        replace = regex_and_replace[1]
        input = re.sub(regex, replace, input)
    return input

YOUTUBE_1 = re.compile("\[\s*(http://)?(www\.)?youtube\.com/watch\?v=([a-zA-Z0-9-_]+)\s*\]", re.IGNORECASE)
YOUTUBE_2 = re.compile("\[\s*(http://)?(www\.)?youtube\.com/v/([a-zA-Z0-9-_]+)(\?.*)?\s*\]", re.IGNORECASE)

# [http://www.youtube.com/watch?v=XXXXXXXXX]
def handle_custom_tag_youtube(input):
    def form1(input):
        regex = YOUTUBE_1
        replace = '<a href="http://www.youtube.com/watch?v=\\3">'\
                  '<img class="youtube" ytid="\\3" src="http://img.youtube.com/vi/\\3/0.jpg" width="480" height="360">'\
                  '</a>\n<a href="http://www.youtube.com/watch?v=\\3">http://www.youtube.com/watch?v=\\3</a>'
        return re.sub(regex, replace, input)
    def form2(input):
        regex = YOUTUBE_2
        replace = '<a href="http://www.youtube.com/watch?v=\\3">'\
                  '<img class="youtube" ytid="\\3" src="http://img.youtube.com/vi/\\3/0.jpg" width="480" height="360">'\
                  '</a>\n<a href="http://www.youtube.com/watch?v=\\3">http://www.youtube.com/watch?v=\\3</a>'
        return re.sub(regex, replace, input)
    input = form1(input)
    input = form2(input)
    return input

MP3 = re.compile("\[([^\]]+mp3)\]", re.IGNORECASE)

# [dir/cool track.mp3]
def handle_custom_tag_mp3(input):
    def replacer(m):
        mp3_name = re.sub(r'^.*/', '', m.group(1))
        mp3_link = "http://dl.dropbox.com/u/%s/sg/%s" % (defs.DROPBOX_USER, urllib2.quote(m.group(1), safe='/'))
        swf = my_tags.static_resource('dewplayer-mini.swf')
        flash = "<object width='160' height='18'><embed src='" + swf + "' width='160' height='18' type='application/x-shockwave-flash' flashvars='&mp3=" + mp3_link + "' quality='high'></embed></object>"
        dl = "<a href=\"%s\">%s</a>" % (mp3_link, mp3_name)
        return "%s %s" % (flash, dl)
    regex = MP3
    return re.sub(regex, replacer, input)

MIXCLOUD = re.compile("\[\s*(http://)?(www.)?mixcloud.com/([a-zA-Z0-9-]+)/([a-zA-Z0-9-]+)/?\s*\]", re.IGNORECASE)

# [http://www.mixcloud.com/user/mixname/]
def handle_custom_tag_mixcloud(input):
    replace  = '<object height="400" width="400"><param name="movie" value="http://www.mixcloud.com/media/swf/player/mixcloudLoader.swf?feed=http%3A%2F%2Fwww.mixcloud.com%2F\\3%2F\\4%2F&amp;embed_uuid=3b4627b1-74e1-43ef-bc52-717acca644d4&amp;embed_type=widget_standard"><param name="allowFullScreen" value="true"><param name="allowscriptaccess" value="always"><embed src="http://www.mixcloud.com/media/swf/player/mixcloudLoader.swf?feed=http%3A%2F%2Fwww.mixcloud.com%2F\\3%2F\\4%2F&amp;embed_uuid=3b4627b1-74e1-43ef-bc52-717acca644d4&amp;embed_type=widget_standard" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true" height="400" width="400"></object>'
    return re.sub(MIXCLOUD, replace, input)

SC_TRACK = re.compile("\[\s*soundcloud\s+([0-9]+)\s*\]", re.IGNORECASE)

# [soundcloud 12345]
def handle_custom_tag_soundcloud_track(input):
    replace  = '''<object height="81" width="100%"><param name="movie" value="https://player.soundcloud.com/player.swf?url=http%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F\\1&amp;show_comments=true&amp;auto_play=false&amp;color=ff7755"></param><param name="allowscriptaccess" value="always"></param><embed allowscriptaccess="always" height="81" src="https://player.soundcloud.com/player.swf?url=http%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F\\1&amp;show_comments=true&amp;auto_play=false&amp;color=ff7700" type="application/x-shockwave-flash" width="100%"></embed></object>'''
    return re.sub(SC_TRACK, replace, input)

SC_PLAYLIST = re.compile("\[\s*soundcloud-playlist\s+([0-9]+)\s*\]", re.IGNORECASE)

# [soundcloud-playlist 12345]
def handle_custom_tag_soundcloud_playlist(input):
    replace  = '<object height="115" width="100%"><param name="movie" value="http://player.soundcloud.com/player.swf?url=http%3A%2F%2Fapi.soundcloud.com%2Fplaylists%2F\\1&amp;amp;show_comments=false&amp;amp;auto_play=false&amp;amp;show_playcount=false&amp;amp;show_artwork=false&amp;amp;color=ff7700"><param name="allowscriptaccess" value="never"><embed height="115" src="http://player.soundcloud.com/player.swf?url=http%3A%2F%2Fapi.soundcloud.com%2Fplaylists%2F\\1&amp;amp;show_comments=false&amp;amp;auto_play=false&amp;amp;show_playcount=false&amp;amp;show_artwork=false&amp;amp;color=ff7700" type="application/x-shockwave-flash" width="100%" allowscriptaccess="never"></embed></object>'
    return re.sub(SC_PLAYLIST, replace, input)

MP3_PLAYLIST = re.compile('\[dewplaylist\s+([^\]]+playlist)\]', re.IGNORECASE)

# [dew.playlist]
def handle_custom_tag_playlist(input):
    swf = my_tags.static_resource('dewplayer-playlist.swf')
    replace = '<object width="240" height="200"><embed src="%s" width="240" height="200" type="application/x-shockwave-flash" flashvars="&xml=http://dl.dropbox.com/u/%s/sg/\\1&autoreplay=1" quality="high"></embed></object>' % (swf, defs.DROPBOX_USER)
    return re.sub(MP3_PLAYLIST, replace, input)

def markup2html_paragraph(markup_text, rich_markup = True, recognize_links = True):
    html = markup_text
    if rich_markup and recognize_links:
        html = handle_custom_tag_http_link(html)
    if rich_markup:
        html = handle_custom_tag_image(html)
        html = handle_custom_tag_mp3(html)
        html = handle_custom_tag_playlist(html)
        html = handle_custom_tag_youtube(html)
        html = handle_custom_tag_mixcloud(html)
        html = handle_custom_tag_soundcloud_track(html)
        html = handle_custom_tag_soundcloud_playlist(html)
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
    class CleverMarkupFailedToMatchInput(Exception):
        pass
    def __init__(self, for_comment, rich_markup = True, recognize_links = True):
        SimpleMarkup.__init__(self, for_comment, rich_markup, recognize_links)
        self.article_id = None
    def generate_html(self, markup_text):
        if self.for_comment:
            return SimpleMarkup.generate_html(self, markup_text)
        pp = break_into_paragraphs(markup_text)
        before, named, after = pp.break_into_three_groups(self.RECOGNIZED_PARAGRAPH_NAMES)
        def para2html(paragraph):
            return markup2html_paragraph(paragraph.body)
        rv = {
            'before': map(para2html, before),
            'middle': self.get_the_middle(pp),
            'after':  map(para2html, after)
        }
        return rv
    def get_the_middle(self, pp):
        def break_tracklist_into_sides(text):
            m = re.search('^(.*)(B0?1\.?\s.*)$', text, re.MULTILINE|re.IGNORECASE|re.DOTALL)
            if m:
                return markup2html_paragraph(m.group(1).strip()),\
                       markup2html_paragraph(m.group(2).strip())
            else:
                return None, None
        hash = {}

        for name in self.RECOGNIZED_PARAGRAPH_NAMES:
            p = pp.get_named_paragraph(name)
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
        return hash if len(hash) > 0 else None

# main function
#@utils.dump_execution_time
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
        return SimpleMarkup(for_comment=False).generate_html(markup)
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

class TestSpacesAfterBR(unittest.TestCase):
    def test_some(self):
        markup = '''
01. track 01
02. track 02
03. track 03

xxx
'''
        print SimpleMarkup(False).generate_html(markup)

if __name__ == '__main__':
    unittest.main()
    #TestCleverMarkup().test_some()