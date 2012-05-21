import os
import utils

HTML_ENCODING = 'UTF-8'

BLOG_NAME = 'Soviet Groove'
BLOG_OWNER = 'Soviet Groove'

DROPBOX_USER = '1883230'
DROPBOX_LOCAL_DIR = 'D:/dropbox/Public/sg'

EXTERNAL_FEEDBACK_LINK = 'http://sovietgroove.userecho.com/'

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

_is_production = {
    'PRODUCTION': True,
    'DEVELOPMENT': False,
}
print 'os.getenv("SERVER_PROFILE"): %s' % os.getenv('SERVER_PROFILE')
PRODUCTION = _is_production[os.getenv('SERVER_PROFILE', 'Env var SERVER_PROFILE not set')]
DEVSERVER = not PRODUCTION

if PRODUCTION:
    CANONICAL_BLOG_URL = 'http://www.sovietgroove.com'
else:
    CANONICAL_BLOG_URL = 'http://localhost:8080'


APP_VERSION = str(utils.get_seconds_since_epoch())

#IMAGE_PLACEHOLDER = '/static/cover.jpg'
IMAGE_PLACEHOLDER = None

EMAIL_NOTIFY_COMMENT = True

PROJECT_DIR = os.path.dirname(__file__)
MARKDOWN_DIR        = os.path.join(PROJECT_DIR, 'operaimport', 'markdown')
STATIC_HTML_DIR     = os.path.join(PROJECT_DIR, 'html')
STATIC_HTML_TAG_DIR = os.path.join(PROJECT_DIR, 'html', 'tag')

FORMAT_YMD_HMS = "%Y-%m-%d %H:%M:%S"