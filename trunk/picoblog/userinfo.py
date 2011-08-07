from google.appengine.api import users

class UserInfo:
    def __init__(self, request):
        self.user = users.get_current_user()
        self.is_admin = users.is_current_user_admin()
        self.login_url = users.create_login_url(request.path)
        self.logout_url = users.create_logout_url(request.path)