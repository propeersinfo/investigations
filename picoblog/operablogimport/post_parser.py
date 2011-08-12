import re
from BeautifulSoup import BeautifulSoup, NavigableString
from soupselect import select
import sys
import datetime
import codecs

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
        if hasattr(a, 'href'):
            del(a['rel'])
            del(a['target'])

def replace_links_with_text_equal_to_href(root):
    for a in root.findAll("a"):
        if hasattr(a, 'href'):
            href = a['href']
            if re.search(r'rapidshare|narod|sendspace|ifolder', href, re.IGNORECASE):
                replacement = "%s" % href
                a.replaceWith(NavigableString(replacement))

def replace_br(root):
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
  return unicode(navString).replace('&amp;', '&')

def parse_date_string(sdate):
    # Example: Thursday, 21. July, 22:31
    # Example: Friday, 28. August 2009, 22:30
    # Example: 28. August 2009, 22:30
    for fmt in ("%A, %d. %B, %H:%M", "%A, %d. %B %Y, %H:%M", "%d. %B %Y, %H:%M"):
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
  fix_single_mp3_player(div_content_node)
  fix_playlist_mp3_player(div_content_node)
  remove_single_mp3_link(div_content_node)
  fix_image(div_content_node)
  fix_youtube(div_content_node)
  fix_mixcloud(div_content_node)
  replace_links_with_text_equal_to_href(div_content_node)
  replace_br(div_content_node)
  fix_links_attrs(div_content_node)
  text = node_to_string(div_content_node)
  text = text.replace('&amp;', '&')
  return text

def node_to_string(root):
    text = ''.join([e for e in root.recursiveChildGenerator() if isinstance(e,unicode)])
    #text = "".join(map(to_string, root.contents))
    return text

#def fix_content(tags):
#    def fix_link_attributes(tag):
#        # elminate rel=nofollow and target=_blank
#        if hasattr(tag, 'name') and tag.name == 'a':
#            tag['rel'] = ''
#            tag['target'] = ''
#        return tag
#    def tags_to_strings(tags):
#        strings = []
#        for tag in tags:
#            if tag:
#                strings.append(str(tag))
#        return strings
#    tags = map(fix_br, tags)
#    tags = map(fix_link_attributes, tags)
#    #for tag in tags:
#    #    print "TYPE:", type(tag)
#    string = "".join(map(to_string, tags))
#    #string = string.replace(' rel=""', ' ')    # see fix_link_attributes()
#    #string = string.replace(' target=""', ' ') # see fix_link_attributes()
#    return string

def get_comments(soup):
    def is_owner_comment(div_text):
        if div_text and div_text.parent and hasattr(div_text.parent, 'class'):
            if div_text.parent['class'].find("owner") >= 0:
                return True
        return False
    def get_text(div_text):
        if div_text:
            tags = div_text.contents
            tags = map(fix_br, tags)
            text = "".join(map(to_string, tags)).strip()
            return text
        else:
            return None
    def get_date(comment_div):
        sdate = select(comment_div, 'span.comment-date')[0].contents[1].strip()
        return parse_date_string(sdate)
    def get_username(comment):
        userlink = select(comment, 'a.userlink')
        if userlink:
            return to_string(userlink[0].contents[0])
        else:
            return None
    comments = []
    for comment_div in soup.findAll("div", {'class': re.compile(r'comment[0-9]')}):
        div_text = comment_div.find("div", {'class': 'text'})
        if div_text:
            flatten_some_tags(div_text)
            text = get_text(div_text)
            owner_comment = is_owner_comment(div_text)
            date = get_date(comment_div)
            username = get_username(comment_div)
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

# TODO: implement comments

def fix_single_mp3_player(root):
    for object_tag in root.findAll("object"):
        for dir in ('sg', 'my'):
            m = re.search(r'http://dl.(get)?dropbox.com/u/1883230/%s/.*mp3' % dir, str(object_tag))
            if m:
                mp3 = m.group(0).replace("http://dl.getdropbox.com/u/1883230/%s/" % dir, "")\
                                .replace("http://dl.dropbox.com/u/1883230/%s/" % dir, "")\
                                .replace("%20", " ")
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
    for tag in root.findAll("object"):
        m = re.search(r'http://www.youtube.com/v/[^&\"]+', str(tag))
        if m:
            tag.replaceWith("[%s]" % m.group(0))

def fix_mixcloud(root):
    for tag in root.findAll("div"):
        if tag.object:
            s = str(tag)
            f = re.search(r'http://www.mixcloud.com/zencd/[^/]+/', s)
            if f:
                tag.replaceWith("[%s]" % f.group(0))

def parse_file(opera_blog_post_file):
  soup = BeautifulSoup(read_file(opera_blog_post_file))
  return {'title' : parse_title(soup),
          'date' : parse_date(soup),
          'tags' : parse_tags(soup),
          'content' : get_content(soup),
          'comments' : get_comments(soup)}

if __name__ == '__main__':
    #file = '75'
    #file = 'ludvikovsky-and-garanian-1971'
    #file = 'soviet-electro-mixtype'
    file = 'raw-funk-from-armenia-1979'
    parsed = parse_file('../operabloghtml/%s' % file)
    print parsed['title'].encode('ascii', 'ignore')
    print parsed['content'].encode('ascii', 'ignore')