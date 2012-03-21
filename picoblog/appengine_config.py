#using_profiler = True
#
#from gae_mini_profiler import profiler
#gae_mini_profiler_ENABLED_PROFILER_EMAILS = ['zeencd@gmail.com']
#
#def webapp_add_wsgi_middleware(app):
#    """Called with each WSGI handler initialisation"""
#    #app = gae_mini_profiler.profiler.ProfilerWSGIMiddleware(app)
#    app = profiler.ProfilerWSGIMiddleware(app)
#    return app
