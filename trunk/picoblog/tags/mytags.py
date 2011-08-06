from google.appengine.ext.webapp import template

from typographus import Typographus

register = template.create_template_register()

@register.filter(name='wld')
def wld(result):
  if result == 1 : return "win"
  if result == 0 : return "loss"
  if result == 0.5 : return "draw"
  return "unknown"

@register.filter(name='typographus')
def typographus(s):
  if not isinstance(s, unicode):
    s = unicode(s)
  return Typographus().process(s)
