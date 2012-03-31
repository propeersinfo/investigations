#using_profiler = True
#
#from gae_mini_profiler import profiler
#gae_mini_profiler_ENABLED_PROFILER_EMAILS = ['zeencd@gmail.com', 'test@example.com']
#
#def webapp_add_wsgi_middleware(app):
#    """Called with each WSGI handler initialisation"""
#    #app = gae_mini_profiler.profiler.ProfilerWSGIMiddleware(app)
#    app = profiler.ProfilerWSGIMiddleware(app)
#    return app

appstats_MAX_STACK = 20

#def appstats_normalize_path(path):
#    return path
#
#def appstats_extract_key(request):
#    key = appstats_normalize_path(request.http_path())
#    #if request.http_method() != 'GET':
#    key = '!!!!!!!!!!!!!!! %s %s' % (request.http_method(), key)
#    return key

# appstats
def webapp_add_wsgi_middleware(app):
    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)
    return app