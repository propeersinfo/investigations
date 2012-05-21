import os
import re
import urllib2
import Image

import defs
import my_tags

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

def handle_custom_tag_image(text, config = None):
    #replacement = '<img src="http://dl.dropbox.com/u/%s/sg/\\1" alt="\\1">' % defs.DROPBOX_USER
    #replacement = '<img src="/static/cover.jpg" width="140" alt="\\1">'
    #return regex.sub(replacement, text)
    def replacer(m):
        addr = m.group(1).strip()
        if addr.startswith('http'):
            return '<img src="%s">' % addr
        else:
            url = 'http://dl.dropbox.com/u/%s/sg/%s' % (defs.DROPBOX_USER, addr)
            image_file = os.path.join(defs.DROPBOX_LOCAL_DIR, addr)

            do_resize = ('cover140px' in config) if config else False
            if do_resize:
                THUMBNAIL_DIR = os.path.join(defs.DROPBOX_LOCAL_DIR, 'img', '140px')
                thumbnail_file = os.path.join(THUMBNAIL_DIR, addr)

                if not os.path.exists(thumbnail_file):
                    th_size = 140, 140
                    img = Image.open(image_file)
                    img.thumbnail(th_size, Image.ANTIALIAS)
                    img.save(thumbnail_file, "JPEG")

                # rewrite url and file
                url = 'http://dl.dropbox.com/u/%s/sg/img/140px/%s' % (defs.DROPBOX_USER, addr)
                image_file = thumbnail_file

            img = Image.open(image_file)
            image_w, image_h = img.size
            return '<img src="%s" width="%s" height="%s" alt="%s">' % (url, image_w, image_h, addr)
    if not defs.IMAGE_PLACEHOLDER:
        return re.sub(CUSTOM_TAG_IMAGE, replacer, text)
    else:
        return re.sub(CUSTOM_TAG_IMAGE, '<img src="%s">' % defs.IMAGE_PLACEHOLDER, text)

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

MP3_PLAYLIST = re.compile('\[dewplaylist\s+([^\]]+)\]', re.IGNORECASE)

# [dew.playlist]
def handle_custom_tag_playlist(input):
    # NB: this does not work when the player and xml are placed at different domains
    #swf = my_tags.static_resource('dewplayer-playlist.swf')
    swf = "http://dl.dropbox.com/u/%s/%s" % (defs.DROPBOX_USER, 'dewplayer-playlist.swf')
    replace = '<object width="240" height="200"><embed src="%s" width="240" height="200" type="application/x-shockwave-flash" flashvars="&xml=http://dl.dropbox.com/u/%s/sg/\\1&autoreplay=1" quality="high"></embed></object>' % (swf, defs.DROPBOX_USER)
    return re.sub(MP3_PLAYLIST, replace, input)

def markup2html_paragraph(markup_text, rich_markup = True, recognize_links = True, config = None):
    html = markup_text
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
    html = html.replace('\n', '<br>\n') # NB: the last transformation
    return html
