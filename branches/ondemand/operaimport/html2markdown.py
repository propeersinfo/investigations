import os
import glob

from post_parser import parse_file

IMPORT_LIMIT = None

MARKDOWN_DIR = 'markdown'
OPERA_HTML_DIR = 'D:/docs/opera-import/opera-blog-copying/operabloghtml'

#class Article(dict):
#    def __init__(self, *args, **kwargs):
#        super(Article, self).__init__()
#        assert len(args) == 0
#        for key in kwargs:
#            self[key] = kwargs[key]


class MarkdownFile():
    def __init__(self, fname):
        self.f = open(fname, 'w')
        self.encoding = 'utf-8'

    def close(self):
        self.f.close()

    def writeln(self, unicode_str):
        s = unicode_str + '\n'
        self.f.write(s.encode(self.encoding))


'''
post['title'],
post['slug'],
post['content'],
post['date'],
post['tags'],
'''

def convert_post_object_to_markdown_file(post):
    md_file = os.path.join(MARKDOWN_DIR, post['slug'])
    f = MarkdownFile(md_file)
    f.writeln('# title: %s' % post['title'])
    f.writeln('# date:  %s' % post['date'])
    f.writeln('# tags:  %s' % ', '.join(post['tags']))
    f.writeln('')
    f.writeln('%s' % post['content'])
    f.close()


def convert_file(fname):
    print '%s...' % fname
    post = parse_file(fname)
    convert_post_object_to_markdown_file(post)


def convert_all_files():
    cnt = 0
    files = glob.glob('%s/*' % OPERA_HTML_DIR)
    for file in files:
        if IMPORT_LIMIT and cnt >= IMPORT_LIMIT: break
        if not os.path.isfile(file): continue
        #import_post_object(parse_file(file))
        convert_file(file)
        cnt += 1


if __name__ == "__main__":
    convert_all_files()
    #convert_file(os.path.join(OPERA_HTML_DIR, 'visitors'))
