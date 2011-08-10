import cgi
from google.appengine.ext import webapp

from django import template as django_template
from django.template import resolve_variable, Node, TemplateSyntaxError, VariableDoesNotExist

register = webapp.template.create_template_register()

###################

def static(static_files_info, path):
  file_version = static_files_info.get(path, 0)
  return '/%s/%s/%s' % ('pseudo-static', file_version, path)
register.simple_tag(static)
