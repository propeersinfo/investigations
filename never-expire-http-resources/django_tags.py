from google.appengine.ext import webapp

from static_files import StaticFilesInfo

register = webapp.template.create_template_register()

def static(path):
    return StaticFilesInfo.get_resource_path(path)

register.simple_tag(static)
