from google.appengine.api import memcache
import logging

class PersistentMemcacheEntity():
    def __init__(self):
        self.value = 'hello'
        logging.info('__init__ called for %s' % id(self))
    def __del__(self):
        logging.info('__del__ called  for %s' % id(self))

def update_memcache(out):
    key = 'the_key'

    logging.info('--------------------')

    obj = memcache.get(key)
    if obj:
        del obj
        logging.info('obj deleted')

    memcache.add(key, PersistentMemcacheEntity(), 10)
    memcache.capabili
    out.write('value set to memcache')

def main():
    logging.getLogger().setLevel(logging.DEBUG)

if __name__ == '__main__':
    main()