# importing - files to check later:
# attention-soviet-grooves          @todo too many blank lines

import glob
import os
import re
import urllib2
from BeautifulSoup import BeautifulSoup, NavigableString
from soupselect import select
import sys
import datetime
import codecs
import HTMLParser
import urllib

def last_file_name(f):
  return re.sub('.*[/\\\]', '', f)

def unescape_html(s):
  # replace html entities
  return HTMLParser.HTMLParser().unescape(s)

def strip_tags(soup, valid_tags = []):
  # modify given BeautifulSoup instance
  # leaving only nodes from valid_tags
  for tag in soup.findAll(True):
    if not tag.name in valid_tags: 
      tag.replaceWithChildren()

def strip_all_tags(html):
  return ''.join(BeautifulSoup(html).findAll(text=True))

def to_string(obj):
    return unicode(obj)

def flatten_some_tags(root):
    for a in root.findAll("a"):
        if hasattr(a, 'href'):
            repl = " %s " % a['href']
            a.replaceWith(NavigableString(repl))

def fix_links_attrs(root):
    # elminate rel=nofollow and target=_blank
    for a in root.findAll("a"):
        del(a['rel'])
        del(a['target'])
        del(a['style'])

def replace_links_with_text_equal_to_href(root):
    for a in root.findAll("a"):
        if hasattr(a, 'href'):
            href = a['href'].strip()
            text = (''.join(a.findAll(text=True))).strip()
            if href == text:
                replacement = "%s" % href
                a.replaceWith(NavigableString(replacement))
            #elif re.search(r'rapidshare|narod|sendspace|ifolder', href, re.IGNORECASE):
            #    # todo: temporary!
            #    raise Exception('non-replaced link to rapidshare|narod|sendspace|ifolder')

# def replace_links_with_text_equal_to_href(root):
#     for a in root.findAll("a"):
#         if hasattr(a, 'href'):
#             href = a['href']
#             #print 'found an <a>'
#             if re.search(r'rapidshare|narod|sendspace|ifolder', href, re.IGNORECASE):
#                 replacement = "%s" % href
#                 a.replaceWith(NavigableString(replacement))

def fix_local_link_url(root):
  for a in root.findAll('a'):
    if hasattr(a, 'href'):
      # fix local links: appropriate for single articles
      a['href'] = a['href'].strip()
      a['href'] = re.sub('^http://my\.opera\.com/sovietgroove/blog/', '/', a['href'])
      a['href'] = re.sub('^/index.dml\?tag=(.+)', '/tag/\\1', a['href'])
      a['href'] = re.sub('^/index.dml/tag/(.+)', '/tag/\\1', a['href'])

def replace_brs(root):
    for a in root.findAll("br"):
        a.replaceWith(NavigableString("\n"))

def fix_br(tag):
    if hasattr(tag, 'name') and tag.name == 'br':
        return '\n'
    return tag

def read_file(path, charset = "utf-8"):
  f = codecs.open(path, "r", charset)
  try:
    return f.read()
  finally:
    f.close()

def parse_title(soup):
  # Path: div#firstpost h2.title
  navString = select(soup, "div#firstpost h2.title")[0].contents[0]
  #return unicode(navString).replace('&amp;', '&')
  s = unicode(navString)
  s = strip_all_tags(s)
  s = unescape_html(s)
  return s

def parse_date_string(sdate):
    # Example: Thursday, 21. July, 22:31
    # Example: Friday, 28. August 2009, 22:30
    # Example: 28. August 2009, 22:30
    # Example: Wednesday, January 13, 2010 12:00:00 PM
    # @see variables: http://pubs.opengroup.org/onlinepubs/007904975/functions/strptime.html
    for fmt in ("%A, %d. %B, %H:%M", "%A, %d. %B %Y, %H:%M", "%d. %B %Y, %H:%M", "%A, %B %d, %Y %H:%M:%S %p"):
      try:
        parsed = datetime.datetime.strptime(sdate, fmt)
        if parsed.year == 1900: parsed = parsed.replace(year = 2011)
        return parsed
      except ValueError:
        pass
    raise Exception("Cannot parse date %s" % sdate)

def parse_date(soup):
  # Path: div#firstpost p.postdate
  # Path: div#firstpost p.postdate a :TEXT:
  postdate_node = select(soup, "div#firstpost p.postdate")[0]
  sdate = postdate_node.contents[0]
  if postdate_node.a:
      sdate = postdate_node.a.contents[0]
  return parse_date_string(sdate)

def parse_tags(soup):
  # Path: div#firstpost p.tags a
  tags = list()
  for a in select(soup, "div#firstpost p.tags a"):
    tags.append(a.contents[0])
  return tags

def get_content(soup):
  # Path: div#main div.content
  div_content_node = select(soup, "div#main div.content")[0]

  #print "".join(map(to_string, div_content_node.contents)).encode('ascii', 'ignore')

  fix_single_mp3_player(div_content_node)
  fix_playlist_mp3_player(div_content_node)
  remove_single_mp3_link(div_content_node)
  fix_image(div_content_node)
  fix_youtube(div_content_node)
  fix_mixcloud(div_content_node)
  fix_soundcloud(div_content_node)
  replace_links_with_text_equal_to_href(div_content_node)
  fix_local_link_url(div_content_node)
  fix_links_attrs(div_content_node)
  strip_tags(div_content_node, valid_tags=['br', 'a', 'ul', 'ol', 'li', 'object', 'param', 'embed'])

  replace_brs(div_content_node)

  no_new_lines_within_objects(div_content_node)

  text = node_to_string(div_content_node)
  text = text.replace('&amp;', '&')

  # not more than two line breaks
  text = re.sub('\n\n\n\n', '\n\n', text)
  text = re.sub('\n\n\n', '\n\n', text)

  text = text.strip()
  
  return text

def node_to_string(root):
    # convert node to HTML string

    # it will leave only text, no tags
    #text = ''.join([e for e in root.recursiveChildGenerator() if isinstance(e,unicode)])

    text = "".join(map(to_string, root.contents))
    return text

def get_comments(soup):
    def is_owner_comment(div_text):
        if div_text and div_text.parent and hasattr(div_text.parent, 'class'):
            if div_text.parent['class'].find("owner") >= 0:
                return True
        return False
    def get_text(div_text, try_to_find_user_name = True):
        if div_text:
            tags = div_text.contents
            tags = map(fix_br, tags)
            text = "".join(map(to_string, tags)).strip()

            if try_to_find_user_name:
              # handle the case when the 1st line is a string like "Blitz writes" and the 2nd one is just empty
              lines = text.split('\n')
              if len(lines) >= 3:
                m = re.match('(.+) writes:', lines[0].strip())
                if m and lines[1].strip() == '':
                  text = '\n'.join(lines[1:])
                  text = text.strip()

            return text
        else:
            return None
    def get_date(comment_div):
        sdate = select(comment_div, 'span.comment-date')[0].contents[1].strip()
        return parse_date_string(sdate)
    def get_username(comment_div, div_text):
        userlink = select(comment_div, 'a.userlink')
        if userlink:
            return unescape_html(to_string(userlink[0].contents[0]))
        else:
            # try to extract username from comment's text like "Blitz writes:"
            text = get_text(div_text, try_to_find_user_name = False)
            if text:
              user_writes = text.split('\n')[0].strip()
              m = re.match('(.+) writes:', user_writes)
              if m:
                return unescape_html(m.group(1))
            return None
    comments = []
    for comment_div in soup.findAll("div", {'class': re.compile(r'comment[0-9]')}):
        div_text = comment_div.find("div", {'class': 'text'})
        if div_text:
            flatten_some_tags(div_text)
            text = get_text(div_text)
            owner_comment = is_owner_comment(div_text)
            date = get_date(comment_div)
            username = get_username(comment_div, div_text)
            comments.append({'username': username,
                             'owner_comment': owner_comment,
                             'date': date,
                             'text': text})
            #print >>sys.stderr, 'username', username
            #print >>sys.stderr, 'div_text', text
            #print >>sys.stderr, "owner_comment:", owner_comment
            #print >>sys.stderr, "date:", date
            #print >>sys.stderr, "------------"
    return comments

# remove new line characters within every OBJECT
def no_new_lines_within_objects(root):
    for object in root.findAll("object"):
        for e in object.findAll(text=True):
            e.replaceWith(NavigableString(unicode(e).strip()))

def fix_single_mp3_player(root):
    for object_tag in root.findAll("object"):
        m = re.search(r'http://dl.(get)?dropbox.com/u/1883230/(sg|my)/(.*mp3)', str(object_tag))
        if m:
            mp3 = urllib2.unquote(m.group(3))
            object_tag.replaceWith(NavigableString("[%s]" % mp3))

def fix_playlist_mp3_player(root):
    for tag in root.findAll("object"):
        if tag.embed and tag.embed['src'] and tag.embed['src'] == 'http://dl.dropbox.com/u/1883230/dewplayer-playlist.swf':
            m = re.search(r'http://dl.dropbox.com/u/1883230/sg/[^&]+', str(tag))
            if m:
                playlist = m.group(0)\
                            .replace("http://dl.getdropbox.com/u/1883230/sg/", "")\
                            .replace("http://dl.dropbox.com/u/1883230/sg/", "")\
                            .replace("%20", " ")
                tag.replaceWith(NavigableString("[dewplaylist %s]" % playlist))

def remove_single_mp3_link(root): # TODO: add: remove only if previous node is a flash (lo priority)
    for tag in root.findAll("a"):
        if re.search(r'dropbox.*mp3', tag['href']):
            tag.extract()

def fix_image(root):
    for tag in root.findAll("img"):
        src = tag['src']
        src = src.replace("http://dl.dropbox.com/u/1883230/sg/", "")
        src = src.replace("%20", " ")
        tag.replaceWith(NavigableString("[%s]" % src))

def fix_youtube(root):
    # form 1: <object>
    for tag in root.findAll("object"):
        m = re.search(r'http://www.youtube.com/v/[^&\"]+', str(tag))
        if m:
            tag.replaceWith("[%s]" % m.group(0))
    # form 2: <iframe>
    # <iframe allowfullscreen="allowfullscreen" src="http://embed.myopera.com/video/?url=http%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DjN4BDPZq8ww&amp;height=344&amp;width=425" frameborder="0" height="350" scrolling="no" width="431">
    # ...watch%3Fv%3DjN4BDPZq8ww&...
    for tag in root.findAll("iframe"):
      if hasattr(tag, 'src'):
        src = tag['src']
        m = re.search('youtube.*watch%3Fv%3D([^&]+)', src)
        if m:
          #print m.group(1)
          #print src
          tag.replaceWith('[http://youtube.com/v/%s]' % m.group(1))

def fix_soundcloud(root):
    # "...playlists%2F24488&..."
    for object in root.findAll("object"):
        if object:
            s = str(object)
            m = re.search(r'soundcloud\.com.*playlists%2F(\d+)&', s)
            if m:
                object.replaceWith("[soundcloud %s]" % m.group(1))

def fix_mixcloud(root):
    # form 1: http://www.mixcloud.com/user/title
    for object in root.findAll("object"):
        if object:
            s = str(object)
            m = re.search(r'http://www.mixcloud.com/zencd/[^/]+/', s)
            if m:
                object.replaceWith("[%s]" % m.group(0))

    # form 2: www.mixcloud.com/api/1/cloudcast/zencd/ukrainian-gro
    for object in root.findAll("object"):
        if object:
            m = re.search(r'mixcloud.com/api/1/cloudcast/([^/]+)/([^/\.]+)', str(object))
            if m:
                object.replaceWith("[http://mixcloud.com/%s/%s/]" % (m.group(1), m.group(2)))

    # form 3: feed=http://www.mixcloud.com/zencd/qaya-selection/&
    for object in root.findAll("object"):
        if object:
            s = str(object)
            s = urllib2.unquote(s)
            m = re.search(r'feed=http://www\.mixcloud\.com/([^/]+)/([^/\.&]+)', s)
            if m:
                object.replaceWith("[http://mixcloud.com/%s/%s/]" % (m.group(1), m.group(2)))

def get_slug(file, date):
  if file.find('@') >= 0:
    return "entry-%04d-%02d-%02d" % (int(date.year), int(date.month), int(date.day))
  else:
    return last_file_name(file)

def parse_file(opera_blog_post_file):
  soup = BeautifulSoup(read_file(opera_blog_post_file))
  date = parse_date(soup)
  return {'title' : parse_title(soup),
          'slug' : get_slug(opera_blog_post_file, date),
          'date' : date,
          'tags' : parse_tags(soup),
          'content' : get_content(soup),
          'comments' : get_comments(soup)}

if __name__ == '__main__':
    file = 'gintarine-pora-75'
    if len(sys.argv) >= 2:
      file = sys.argv[1]
    for file in glob.glob('../operabloghtml/%s' % file):
        if not os.path.isfile(file): continue

        print ''
        print '-------------- %s --------------' % file
        print ''

        parsed = parse_file('../operabloghtml/%s' % file)
        print 'title:', (parsed['title']).encode('ascii', 'replace')
        print 'slug:', parsed['slug'].encode('ascii', 'replace')
        print parsed['content'].encode('ascii', 'replace')

#        for c in parsed['comments']:
#           print ''
#           print 'comment: %s -> %s' % (c['username'], c['text'])