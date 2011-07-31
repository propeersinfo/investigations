import re

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

# main function
def markup2html(markup_text, rich_markup = True, recognize_links = True):
    html = markup_text.replace('\n', '<br>\n')
    if recognize_links:
        html = handle_custom_tag_http_link(html)
    if rich_markup:
        html = handle_custom_tag_mp3(html)
        html = handle_custom_tag_youtube(html)
        html = handle_custom_tag_mixcloud(html)
    return html