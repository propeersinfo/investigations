import json
import datetime

import defs # needed for 'import utils'
import utils

DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class CommentDB:
    def __init__(self, filename):
        json_list = json.loads(utils.read_file(filename))
        self.articles_by_path = dict()
        for a in json_list:
            path = a['path']
            comments = a['comments']
            for c in comments:
                if c.has_key('date'):
                    c['date'] = datetime.datetime.strptime(c['date'], DATE_TIME_FORMAT)
            assert not self.articles_by_path.has_key(path), 'duplicate for path %s' % path
            self.articles_by_path[path] = comments

    instance = None

    @classmethod
    def get_instance(cls, filename):
        #if cls.instance is None:
        #    cls.instance = CommentDB(filename)
        #return cls.instance
        return CommentDB(filename)

    def get_comments_for_path(self, path):
        return self.articles_by_path.get(path)


db = CommentDB('operaimport/comments4json.result.json')
print db.get_comments_for_path('/alexey-mazhukov-1973')