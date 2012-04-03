import datetime
import simplejson as json

import json_helper

class Entity(object):
    def __init__(self):
        super(Entity, self).__init__()
        self.param = 'val'
        self.dt = datetime.datetime.now()
        self.num = 51

    def __str__(self):
        return 'Entity(param=%s,dt=%s,num=%d)' % (self.param, self.dt, self.num)

Entity = json_helper.setup_from_dict(Entity)

TYPES = json_helper.define_json_classes(Entity)

#s = json.dumps(Entity(), cls=CustomTypeEncoder)
o = Entity()
print o
s = json_helper.dumps(o, TYPES)
#s = json.dumps(o, cls=make_encoder(TYPES))
print s
#print json.loads(s, object_hook=make_decoder(TYPES))
print json_helper.loads(s, TYPES)