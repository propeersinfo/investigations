import os

BLOG_NAME = 'Soviet Rare Groove'
BLOG_OWNER = 'Soviet Groove'

DROPBOX_USER = '1883230'

THEME_DIR = 'themes/birman'
TEMPLATE_DIR = 'templates'

TAG_URL_PATH = 'tag'
DATE_URL_PATH = 'date'
#ARTICLE_URL_PATH = 'id'
MEDIA_URL_PATH = 'static'
ATOM_URL_PATH = 'atom'
RSS2_URL_PATH = 'rss'
ARCHIVE_URL_PATH = 'archive'

MAX_ARTICLES_PER_PAGE = 10
TOTAL_RECENT = 10

if os.environ.get('SERVER_SOFTWARE','').lower().find('development') >= 0:
  PRODUCTION = False
  CANONICAL_BLOG_URL = 'http://localhost:8080/'
else:
  PRODUCTION = True
  CANONICAL_BLOG_URL = 'http://sovietraregroove.appspot.com/'
