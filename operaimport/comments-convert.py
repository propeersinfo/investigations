import codecs
import glob
import os
import json
from jinja2 import Environment, FileSystemLoader
import sys
from operaimport.post_parser import parse_file

OPERA_HTML_DIR = 'D:/docs/opera-import/opera-blog-copying/operabloghtml'
URL_BASE = 'http://www.sovietgroove.com'

def write_file(path, content):
    if type(content) == unicode:
        content = unicode(content).encode('utf-8')
    f = codecs.open(path, "wb")
    try:
        return f.write(content)
    finally:
        f.close()

def render_template(template_name, vars):
    env = Environment(loader=FileSystemLoader('.'))
    def json_value(value):
        #return value.replace('"', '\\"')
        return json.dumps(value)
    env.filters['json_value'] = json_value
    return env.get_template(template_name).render(vars)

# article: ['tags', 'title', 'comments', 'content', 'date', 'slug']
# comment: username, text, date

if __name__ == '__main__':
    tpl_name = sys.argv[1]
    res_file = sys.argv[2]

    articles = list()
    com_cnt = 0
    OFFSET = 0
    for html_file in glob.glob('%s/*' % OPERA_HTML_DIR):
        print html_file
        article = parse_file(html_file)
        cc = article['comments']
        if len(cc) > 0:
            articles.append(article)
            for c in cc:
                com_cnt += 1
                c['fake_id'] = com_cnt + OFFSET
                print c['fake_id']
        else:
            print '-skipping-0-comments-'

        #if com_cnt > 10: break

    print 'there are %d articles' % (len(articles))
    print 'there are %d comments' % (com_cnt,)

    tpl_vars = {
        'articles': articles,
        'URL_BASE': URL_BASE,
    }
    xml = render_template(tpl_name, tpl_vars)
    write_file(res_file, xml)
