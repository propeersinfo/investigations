from google.appengine.ext import webapp

def blog_tag(blog_tag_name, blog_tag_title = None):
  if not blog_tag_title:
    blog_tag_title = blog_tag_name
  return '<a href="/tag/%s">%s</a>' % (blog_tag_name, blog_tag_title)

register = webapp.template.create_template_register()
register.simple_tag(blog_tag)