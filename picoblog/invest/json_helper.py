import datetime
import simplejson as json

DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

def dumps(object, types):
    return json.dumps(object, cls=make_encoder(types))

def loads(input, types):
    return json.loads(input, object_hook=make_decoder(types))

def setup_from_dict(original_class):
    def from_dict(dct):
        obj = original_class()
        for key in dct.keys():
            value = dct[key]
            try:
                value = datetime.datetime.strptime(value, DATE_TIME_FORMAT)
            except ValueError:
                pass
            except TypeError:
                pass
            setattr(obj, key, value)
        return obj
    setattr(original_class, from_dict.__name__, staticmethod(from_dict))
    return original_class

def define_json_classes(*classes):
    dct = dict()
    for cls in classes:
        assert hasattr(cls, 'from_dict')
        dct['__%s__' % cls.__name__] = cls
    return  dct

def make_encoder(types):
    class ParametrizedTypeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, *(types.values())):
                key = '__%s__' % obj.__class__.__name__
                return { key: obj.__dict__ }
            elif isinstance(obj, datetime.datetime):
                return obj.strftime(DATE_TIME_FORMAT)
            else:
                return json.JSONEncoder.default(self, obj)
    return ParametrizedTypeEncoder

def make_decoder(types):
    def decoder(dct):
        if len(dct) == 1:
            type_name, value = dct.items()[0]
            if type_name in types:
                type = types[type_name]
                return type.from_dict(value)
        return dct
    return decoder
