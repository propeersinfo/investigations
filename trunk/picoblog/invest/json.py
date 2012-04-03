import datetime
import simplejson as json
#import json

class Entity(object):
    def __init__(self):
        super(Entity, self).__init__()
        self.param = 'val'
        self.dt = datetime.datetime.now()
        self.num = 51

    def __str__(self):
        return 'Entity(param=%s,dt=%s)' % (self.param, self.dt)

    @classmethod
    def from_dict(cls, dct):
        obj = Entity()
        for key in dct.keys():
            value = dct[key]
            try:
                value = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
            except TypeError:
                pass
            setattr(obj, key, value)
        #obj.param = dct.get('param')
        #obj.dt = dct.get('dt')
        return obj

def define_json_classes(*classes):
    dct = dict()
    for cls in classes:
        dct['__%s__' % cls.__name__] = cls
    return  dct

TYPES = define_json_classes(Entity)

def make_encoder(types):
    class ParametrizedTypeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, *(types.values())):
                key = '__%s__' % obj.__class__.__name__
                return { key: obj.__dict__ }
            elif isinstance(obj, datetime.datetime):
                return obj.strftime("%Y-%m-%d %H:%M:%S")
            return json.JSONEncoder.default(self, obj)
    return ParametrizedTypeEncoder

def make_decoder(types):
    def decoder(dct):
        if len(dct) == 1:
            type_name, value = dct.items()[0]
            #type_name = type_name.strip('_')
            if type_name in types:
                return types[type_name].from_dict(value)
        return dct
    return decoder

#s = json.dumps(Entity(), cls=CustomTypeEncoder)
o = Entity()
print o
s = json.dumps(o, cls=make_encoder(TYPES))
print s
print json.loads(s, object_hook=make_decoder(TYPES))