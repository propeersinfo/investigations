# -*- coding: utf-8 -*-

from StringIO import StringIO
import sys
import unicodedata


def normalize_unicode_except_cyrillic(s):
  res = StringIO()
  for ch in unicodedata.normalize('NFKD', s):
    n = ord(ch)
    ascii = 0 <= n < 128
    cyr_lo = ord(u'а') <= n <= ord(u'я')
    cyr_hi = ord(u'А') <= n <= ord(u'Я')
    if ascii or cyr_lo or cyr_hi:
      res.write(ch)
  return res.getvalue()


class StreamTee:
  """Intercept a stream."""

  def __init__(self, target):
    self.target = target

  def write(self, s):
    s = self.intercept(s)
    self.target.write(s)

  def intercept(self, s):
    """Pass-through -- Overload this."""
    return s

  def flush(self):
    return self.target.flush()


class SafeStreamFilter(StreamTee):
  """Convert string traffic to to something safe."""

  def __init__(self, target):
    StreamTee.__init__(self, target)
    self.encoding = 'utf-8'
    self.errors = 'replace'
    self.encode_to = self.target.encoding
    #if self.encode_to == 'cp65001':
    #  self.encode_to = 'utf-8'
    print 'self.encode_to:', self.encode_to
    #if not self.encode_to:
    #  #raise Exception('target.encoding is None (because of redirect)')
    #  self.encode_to = 'cp866'

  def intercept(self, s):
    if self.encode_to:
      return s.encode(self.encode_to, self.errors).decode(self.encode_to)
    else:
      return s

  @classmethod
  def substitute_stdout(cls):
    sys.stdout = SafeStreamFilter(sys.stdout)


class dict_of_lists(dict):
  def __init__(self):
    super(dict_of_lists, self).__init__()

  def append(self, key, value):
    if self.has_key(key):
      assert isinstance(self[key], list)
      self[key].append(value)
    else:
      self[key] = [value]


def format_size(num):
  for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
    if num < 1024.0:
      return "%3.0f%s" % (num, x)
    num /= 1024.0


def format_size_mb(num):
  num = num / 1024.0 / 1024.0
  return "%3.0f" % (num)


# format an str/unicode json-string as one readable by humans
# because the standard json.sumps() produces all these '\xUUUU'
def pretty_print_json_as_readable_unicode(json_object):
  def do_level(out, root, level=0):
    offset = '  ' * level
    offset2 = '  ' * (level + 1)
    if isinstance(root, list):
      out.write('%s[\n' % (offset,))
      for i, item in enumerate(root):
        if i > 0: out.write('%s,\n' % offset)
        do_level(out, item, level + 1)
      out.write('\n%s]' % (offset,))
    elif isinstance(root, dict):
      out.write('%s{\n' % (offset,))
      keys = sorted(root.keys())
      for i, key in enumerate(keys):
        if i > 0: out.write('%s,\n' % '')
        out.write('%s"%s": ' % (offset2, key))
        do_level(out, root[key], level + 1)
      out.write('\n%s}' % offset)
    elif isinstance(root, basestring):
      root = root.replace('\\', '\\\\').replace('"', '\\"').replace('\r', '\\r').replace('\n', '\\n')
      out.write('"%s"' % (root,))
    elif isinstance(root, (float)):
      out.write('%s%s' % (offset, repr(root))) # NB: repr is a must for fp numbers
    elif isinstance(root, (int, long)):
      out.write('%s%s' % (offset, root))
    else:
      raise Exception('unsupported yet type %s' % type(root))

  #assert isinstance(json_text, (basestring))
  out = StringIO()
  try:
    do_level(out, json_object)
    return out.getvalue()
  finally:
    out.close()

# class counting_hash(dict):
#     def __init__(self):
#         super(counting_hash, self).__init__()
#     def increment(self, key):
#         if self.has_key(key):
#             assert isinstance(self[key], int)
#             self[key] = self[key] + 1
#         else:
#             self[key] = 1


#class CaseInsensitiveDict(dict):
#    def __setitem__(self, key, value):
#        return super(CaseInsensitiveDict, self).__setitem__(key.lower(), value)
#    def __getitem__(self, key):
#        return super(CaseInsensitiveDict, self).__getitem__(key.lower())
#    def get(self, key, default=None):
#        return super(CaseInsensitiveDict, self).get(key.lower(), default)
#    def __contains__(self):
#        raise Exception('is not implemented yet')
#    def has_key(self, key):
#        raise Exception('is not implemented yet')
#
#
