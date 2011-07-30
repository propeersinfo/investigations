from google.appengine.ext import db

class Unique(db.Model):
  @classmethod
  def check(cls, scope, value, throw_exception = True):
    exists = False
    def tx(scope, value):
      key_name = "U%s:%s" % (scope, value,)
      ue = Unique.get_by_key_name(key_name)
      if ue:
        #raise UniqueConstraintViolation(scope, value)
        exists = True
      else:
        ue = Unique(key_name=key_name)
        ue.put()
    db.run_in_transaction(tx, scope, value)
    if throw_exception:
      raise UniqueConstraintViolation(scope, value)
    else:
      return exists

class UniqueConstraintViolation(Exception):
  def __init__(self, scope, value):
    super(UniqueConstraintViolation, self).__init__("Value '%s' is not unique within scope '%s'." % (value, scope, ))