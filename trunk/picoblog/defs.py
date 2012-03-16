import os

HTML_ENCODING = 'UTF-8'

BLOG_NAME = 'Soviet Groove'
BLOG_OWNER = 'Soviet Groove'

DROPBOX_USER = '1883230'

THEME_DIR = 'themes/grid'
TEMPLATE_DIR = '.'

TAG_URL_PATH = 'tag'
DATE_URL_PATH = 'date'
MEDIA_URL_PATH = 'static'
RSS2_URL_PATH = 'rss'
ARCHIVE_URL_PATH = 'archive'

MAX_ARTICLES_PER_PAGE = 5
MAX_ARTICLES_PER_PAGE_ARCHIVE = 50
MAX_ARTICLES_RSS = 10
TOTAL_RECENT = 10

# todo: need to be reviewed
if os.environ.get('SERVER_SOFTWARE','').lower().find('development') >= 0:
  PRODUCTION = False
  CANONICAL_BLOG_URL = 'http://localhost'
else:
  PRODUCTION = True
  CANONICAL_BLOG_URL = 'http://www.sovietgroove.com'

DEVSERVER = not PRODUCTION

APP_VERSION_FOR_UNIT_TESTS = '' # important because None value causes errors in library code further
APP_VERSION = os.getenv('CURRENT_VERSION_ID', APP_VERSION_FOR_UNIT_TESTS)