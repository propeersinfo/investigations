import os
from google.appengine.api import memcache

WHERE_STATIC_FILES_ARE_STORED = 'pseudo-static'
# store cached info for five seconds to allow altering 'static' files
MEMCACHE_TIME_DEV_SERVER = 5
# read info once because there is no chance 'static' files would be changed until next deploy
MEMCACHE_TIME_PRODUCTION = 0

def is_production():
    return os.environ.get('SERVER_SOFTWARE','').lower().find('development') < 0

class StaticFilesInfo():
    @classmethod
    def get_resource_path(cls, resource):
        resource_current_version = cls.__get_static_files_info().get(resource, 0)
        return '/%s/%s/%s' % (WHERE_STATIC_FILES_ARE_STORED, resource_current_version, resource)

    @classmethod
    def __get_static_files_info(cls):
        info = memcache.get(cls.__name__)
        if info is None:
            info = cls.__grab_info()
            time = MEMCACHE_TIME_PRODUCTION if is_production() else MEMCACHE_TIME_DEV_SERVER
            memcache.set(cls.__name__, info, time)
        return info

    @classmethod
    def __grab_info(cls):
        """
        Obtain info about all files in managed 'static' directory.
        This is done rarely.
        """
        dir = os.path.join(os.path.split(__file__)[0], WHERE_STATIC_FILES_ARE_STORED)
        hash = {}
        for file in os.listdir(dir):
            abs_file = os.path.join(dir, file)
            hash[file] = int(os.path.getmtime(abs_file))
        return hash
