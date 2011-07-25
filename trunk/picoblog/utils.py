import os
import re
import unicodedata

def slugify(s):
  s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').lower()
  s = re.sub("[']", '', s)                        # remove some chars
  s = re.sub('[^a-zA-Z0-9-]+', '-', s).strip('-') # replace the rest with '-'
  return s
