import os
import re
import urllib2

from PIL import Image

import defs


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


def handle_custom_tag_image(text, config=None):
    #replacement = '<img src="http://dl.dropbox.com/u/%s/sg/\\1" alt="\\1">' % defs.DROPBOX_USER
    #replacement = '<img src="/static/cover.jpg" width="140" alt="\\1">'
    #return regex.sub(replacement, text)
    def replacer(m):
        addr = m.group(1).strip()
        if addr.startswith('http'):
            return '<img src="%s">' % addr
        else:
            url = 'http://dl.dropboxusercontent.com/u/%s/sg/%s' % (defs.DROPBOX_USER, addr)
            large_url = None
            image_file = os.path.join(defs.DROPBOX_LOCAL_DIR, addr)

            do_resize = ('cover140px' in config) if config else False
            if do_resize:
                thumbnail_file = os.path.join(defs.THUMBNAIL_DIR, addr)

                if not os.path.exists(thumbnail_file):
                    th_size = 140, 140
                    img = Image.open(image_file)
                    img.thumbnail(th_size, Image.ANTIALIAS)
                    img.save(thumbnail_file, "JPEG")

                # rewrite url and file
                large_url = url

                hash_suffix = ''
                # from gen_static import BlogMeta
                # thumbnail_hash = BlogMeta.instance().get_resource_hash(thumbnail_file)
                # if thumbnail_hash:
                #     hash_suffix = '?v=%s' % thumbnail_hash

                url = 'http://dl.dropboxusercontent.com/u/%s/sg/img/140px/%s%s' % (defs.DROPBOX_USER, addr, hash_suffix)
                image_file = thumbnail_file

            img = Image.open(image_file)
            image_w, image_h = img.size
            html = '<img src="%s" width="%s" height="%s" alt="%s">' % (url, image_w, image_h, addr)
            if large_url:
                html = '<a href="%s">%s</a>' % (large_url, html)
            return html

    if not defs.IMAGE_PLACEHOLDER:
        return re.sub(CUSTOM_TAG_IMAGE, replacer, text)
    else:
        return re.sub(CUSTOM_TAG_IMAGE, '<img src="%s">' % defs.IMAGE_PLACEHOLDER, text)


LINK_1 = re.compile('^(https?://[^\s]+)', re.IGNORECASE)    # a link at the most beginning
LINK_2 = re.compile('(\s)(https?://[^\s]+)', re.IGNORECASE) # all other cases

# http://ya.ru/
def handle_custom_tag_http_link(input_str):
    for regex_and_replace in [
        [LINK_1, '<a href="\\1">\\1</a>'],
        [LINK_2, '\\1<a href="\\2">\\2</a>']
    ]:
        regex = regex_and_replace[0]
        replace = regex_and_replace[1]
        input_str = re.sub(regex, replace, input_str)
    return input_str


YOUTUBE_1 = re.compile("\[\s*(http://)?(www\.)?youtube\.com/watch\?v=([a-zA-Z0-9-_]+)\s*\]", re.IGNORECASE)
YOUTUBE_2 = re.compile("\[\s*(http://)?(www\.)?youtube\.com/v/([a-zA-Z0-9-_]+)(\?.*)?\s*\]", re.IGNORECASE)
#YT_DIM = (480, 360)
YT_DIM = (300, 225)


# [http://www.youtube.com/watch?v=XXXXXXXXX]
def handle_custom_tag_youtube(input_str):
    def form1(input_str):
        regex = YOUTUBE_1
        replace = '<a href="http://www.youtube.com/watch?v=\\3">' \
                  '<img class="youtube" ytid="\\3" src="http://img.youtube.com/vi/\\3/0.jpg" width="%d" height="%d">' \
                  '</a>' % YT_DIM
        return re.sub(regex, replace, input_str)

    def form2(input_str):
        regex = YOUTUBE_2
        replace = '<a href="http://www.youtube.com/watch?v=\\3">' \
                  '<img class="youtube" ytid="\\3" src="http://img.youtube.com/vi/\\3/0.jpg" width="%d" height="%d">' \
                  '</a>' % YT_DIM
        return re.sub(regex, replace, input_str)

    input_str = form1(input_str)
    input_str = form2(input_str)
    return input_str


MP3 = re.compile("\[\s*([^\]]+\.mp3)\s*\]", re.IGNORECASE)


# [dir/cool track.mp3]
def handle_custom_tag_mp3(input_str):
    import gen_static

    def replacer(m):
        mp3_name = re.sub(r'^.*/', '', m.group(1))
        mp3_link = "http://dl.dropboxusercontent.com/u/%s/sg/%s" % (
            defs.DROPBOX_USER, urllib2.quote(m.group(1), safe='/'))
        # swf = my_tags.static_resource('dewplayer-mini.swf')
        swf = gen_static.static_resource_filter('dewplayer-mini.swf')
        flash = "<object width='160' height='18'><embed src='" + swf + "' width='160' height='18' type='application/x-shockwave-flash' flashvars='&mp3=" + mp3_link + "&autoplay=1' quality='high'></embed></object>"
        icon = '<a href="%s" class="audio-player" data-swf-html="%s"><img src="/static/play.png" alt="play"></a>' % (
            mp3_link, flash.replace('"', '\\"'))
        dl = "<a href=\"%s\">%s</a>" % (mp3_link, mp3_name)
        return "%s %s" % (icon, dl)

    regex = MP3
    return re.sub(regex, replacer, input_str)


MIXCLOUD = re.compile("\[\s*((http://)?(www.)?mixcloud.com/([a-zA-Z0-9-]+)/([a-zA-Z0-9-]+)/?)\s*\]", re.IGNORECASE)

# [http://www.mixcloud.com/user/mixname/]
def handle_custom_tag_mixcloud(input_str):
    # <object> is not available at mobile
    #replace = u'<object height="300" width="400"><param name="movie" value="http://www.mixcloud.com/media/swf/player/mixcloudLoader.swf?feed=http%3A%2F%2Fwww.mixcloud.com%2F\\4%2F\\5%2F&amp;embed_uuid=3b4627b1-74e1-43ef-bc52-717acca644d4&amp;embed_type=widget_standard"><param name="allowFullScreen" value="true"><param name="allowscriptaccess" value="always"><embed src="http://www.mixcloud.com/media/swf/player/mixcloudLoader.swf?feed=http%3A%2F%2Fwww.mixcloud.com%2F\\4%2F\\5%2F&amp;embed_uuid=3b4627b1-74e1-43ef-bc52-717acca644d4&amp;embed_type=widget_standard" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true" height="300" width="400"></object><p><a href="\\1">The mix at mixcloud&nbsp;\u2197</a></p>'

    # iframe works at mobileun like the object
    replace = u'''<iframe width="100%" height="300" src="//www.mixcloud.com/widget/iframe/?feed=http%3A%2F%2Fwww.mixcloud.com%2F\\4%2F\\5%2F&show_tracklist=&stylecolor=&hide_artwork=&mini=&embed_type=widget_standard&embed_uuid=f4535b1b-4fa1-4c5a-bb9c-665df66bc9c8&hide_cover=" frameborder="0"></iframe><p><a href="\\1">The mix at mixcloud&nbsp;\u2197</a></p>'''

    return re.sub(MIXCLOUD, replace, input_str)


SC_TRACK = re.compile("\[\s*soundcloud\s+([0-9]+)\s*\]", re.IGNORECASE)


# [soundcloud 12345]
def handle_custom_tag_soundcloud_track(input_str):
    # <object> is not available at mobile
    #replace = '''<object height="81" width="100%"><param name="movie" value="https://player.soundcloud.com/player.swf?url=http%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F\\1&amp;show_comments=true&amp;auto_play=false&amp;color=ff7755"></param><param name="allowscriptaccess" value="always"></param><embed allowscriptaccess="always" height="81" src="https://player.soundcloud.com/player.swf?url=http%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F\\1&amp;show_comments=true&amp;auto_play=false&amp;color=ff7700" type="application/x-shockwave-flash" width="100%"></embed></object>'''
    
    # iframe works at mobileun like the object
    replace = '''<iframe width="100%" height="166" scrolling="no" frameborder="no" src="https://w.soundcloud.com/player/?url=http%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F\\1&amp;color=ff6600&amp;auto_play=false&amp;show_artwork=true"></iframe>'''
    
    return re.sub(SC_TRACK, replace, input_str)


SC_PLAYLIST = re.compile("\[\s*soundcloud-playlist\s+([0-9]+)\s*\]", re.IGNORECASE)


# [soundcloud-playlist 12345]
def handle_custom_tag_soundcloud_playlist(input_str):
    # <object> is not available at mobile
    #replace = '<object height="200" width="100%"><param name="movie" value="http://player.soundcloud.com/player.swf?url=http%3A%2F%2Fapi.soundcloud.com%2Fplaylists%2F\\1&amp;amp;show_comments=false&amp;amp;auto_play=false&amp;amp;show_playcount=false&amp;amp;show_artwork=false&amp;amp;color=ff7700"><param name="allowscriptaccess" value="never"><embed height="200" src="http://player.soundcloud.com/player.swf?url=http%3A%2F%2Fapi.soundcloud.com%2Fplaylists%2F\\1&amp;amp;show_comments=false&amp;amp;auto_play=false&amp;amp;show_playcount=false&amp;amp;show_artwork=false&amp;amp;color=ff7700" type="application/x-shockwave-flash" width="100%" allowscriptaccess="never"></embed></object>'

    # iframe works at mobileun like the object
    replace = '''<iframe width="100%" height="350" scrolling="no" frameborder="no" src="https://w.soundcloud.com/player/?url=http%3A%2F%2Fapi.soundcloud.com%2Fplaylists%2F\\1"></iframe>'''

    return re.sub(SC_PLAYLIST, replace, input_str)


MP3_PLAYLIST = re.compile('\[dewplaylist\s+([^\]]+)\]', re.IGNORECASE)


# [dew.playlist]
def handle_custom_tag_playlist(input_str):
    # NB: this does not work when the player and xml are placed at different domains
    #swf = my_tags.static_resource('dewplayer-playlist.swf')
    swf = "http://dl.dropboxusercontent.com/u/%s/%s" % (defs.DROPBOX_USER, 'dewplayer-playlist.swf')
    replace = '<object width="240" height="200"><embed src="%s" width="240" height="200" type="application/x-shockwave-flash" flashvars="&xml=http://dl.dropboxusercontent.com/u/%s/sg/\\1&autoreplay=1" quality="high"></embed></object>' % (
        swf, defs.DROPBOX_USER)
    return re.sub(MP3_PLAYLIST, replace, input_str)

# the order is important
MARKUP_LINK_REGEXPS = [
    # [one two] ~> http://ya.ru
    r'\[([^\]]+)\]\s*~>\s*(http://[\.a-z0-9]+[^\s]+)',
    # one ~> http://ya.ru
    r'([^\s]+)\s*~>\s*(http://[\.a-z0-9]+[^\s]+)'
]


def handle_markup_link(input_str):
    def replacer_text_link(m):
        return '<a href="%s">%s</a>' % (m.group(2), m.group(1))

    for r in MARKUP_LINK_REGEXPS:
        input_str = re.sub(r, replacer_text_link, input_str)
    return input_str


def handle_emphasis(input_str):
    REGEX = ur'((^)|(?<=\s))  \*([^\s][^*]*[^\s])\*  ((?=[\s.,;!?])|($))'
    input_str = re.sub(REGEX, '<em>\\3</em>', input_str, flags=re.VERBOSE)
    return input_str


def markup2html_paragraph(markup_text, rich_markup=True, recognize_links=True, config=None):
    html = markup_text
    if rich_markup:
        html = handle_markup_link(html)
    if rich_markup and recognize_links:
        html = handle_custom_tag_http_link(html)
    if rich_markup:
        html = handle_custom_tag_image(html, config)
        html = handle_custom_tag_mp3(html)
        html = handle_custom_tag_playlist(html)
        html = handle_custom_tag_youtube(html)
        html = handle_custom_tag_mixcloud(html)
        html = handle_custom_tag_soundcloud_track(html)
        html = handle_custom_tag_soundcloud_playlist(html)
    html = handle_emphasis(html)
    html = html.replace('\n', '<br>\n') # NB: the last transformation
    return html


def assert_handle_markup_link(input_str, golden):
    actual = handle_markup_link(input_str)
    if actual != golden:
        print 'test failed'
        print 'golden: %s' % golden
        print 'actual: %s' % actual
        raise Exception('a test failed - execution interrupted')


if __name__ == '__main__':
    assert_handle_markup_link('before text ~> http://ya.ru after', 'before <a href="http://ya.ru">text</a> after')
    assert_handle_markup_link('before text~>http://ya.ru after', 'before <a href="http://ya.ru">text</a> after')
    assert_handle_markup_link('before [one two] ~> http://ya.ru after',
                              'before <a href="http://ya.ru">one two</a> after')
    print 'tests passed'