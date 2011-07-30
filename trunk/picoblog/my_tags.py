from google.appengine.ext import webapp

from django import template as django_template
from django.template import resolve_variable, Node, TemplateSyntaxError, VariableDoesNotExist

register = webapp.template.create_template_register()

###################

def blog_tag(blog_tag_name, blog_tag_title = None):
  if not blog_tag_title:
    blog_tag_title = blog_tag_name
  return '<a href="/tag/%s">%s</a>' % (blog_tag_name, blog_tag_title)

register.simple_tag(blog_tag)

###################

def mytag(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 2:
        raise django_template.TemplateSyntaxError, "Error: len(bits) = %s" % len(bits)
    return MyNode(bits[1])

class MyNode(django_template.Node):
    def __init__(self, my_var):
        self.my_var = my_var
    def render(self, context):
        try:
            my_var = django_template.resolve_variable(self.my_var, context)
        except django_template.VariableDoesNotExist:
            my_var = None
        return "my var is: %s" % my_var

register.tag(mytag)