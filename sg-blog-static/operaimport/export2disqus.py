import codecs
import glob
import os
from jinja2 import Environment, FileSystemLoader
from operaimport.post_parser import parse_file

OPERA_HTML_DIR = 'D:/docs/opera-import/opera-blog-copying/operabloghtml'

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
    return env.get_template(template_name).render(vars)

# article: ['tags', 'title', 'comments', 'content', 'date', 'slug']
# comment: username, text, date

articles = list()
com_cnt = 0
for html_file in glob.glob('%s/*' % OPERA_HTML_DIR):
    print html_file
    #html_file = os.path.join(OPERA_HTML_DIR, 'dos-mukasan-1976')
    article = parse_file(html_file)
    articles.append(article)
    for c in article['comments']:
        #print c['date'].strftime('%Y-%m-%d %H:%M:%S')
        com_cnt += 1
    break

print 'there are %d articles' % (len(articles))
print 'there are %d comments' % (com_cnt,)

tpl_vars = {
    'articles': articles,
}
xml = render_template('export2disqus.tpl.xml', tpl_vars)
write_file('export2disqus.res.xml', xml)
