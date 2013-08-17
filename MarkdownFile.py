import re
import os
import codecs

import defs
import utils
from operaimport.tag_rewrite import rewrite_tag
from operaimport.post_parser import parse_date_string


class MarkdownFile():
    def __init__(self, meta, text):
        self.meta = meta
        self.text = text

    @classmethod
    def parse(cls, file, read_content=True):

        read_content = True  # todo: the param rewritten!

        MD_PROPERTY_REGEX = re.compile('\s*#\s*'  '([a-zA-Z0-9_-]+)'  '\s*:\s*'  '(.*)'  '\s*')
        slug = os.path.split(file)[-1]
        #raise Exception('setting slug to: %s' % (slug,))
        meta = {
            'slug': slug,
            'mtime': os.path.getmtime(file),
        }
        f = codecs.open(file, "r", defs.HTML_ENCODING)
        try:
            while True:
                line = f.readline().strip()
                m = re.match(MD_PROPERTY_REGEX, line)
                if m:
                    key = m.group(1).lower()
                    value = m.group(2)
                    if key == 'tags':
                        value = cls._handle_tags(value)
                    elif key == 'date':
                        value = parse_date_string(value)
                    meta[key] = value
                elif line == '':
                    break
                else:
                    raise Exception('markup file format error for %s -> "%s"' % (file, line))
            text = f.read(6000000).strip() if read_content else None # todo: what the fuck with that read?!
            return MarkdownFile(meta, text)
        finally:
            f.close()

    @classmethod
    def _handle_tags(cls, string_value):
        tags = utils.split_and_strip_tags(string_value.lower(), ',')
        tags = map(rewrite_tag, tags)
        return tags

