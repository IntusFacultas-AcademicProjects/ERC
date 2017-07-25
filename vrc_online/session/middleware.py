from django.http import HttpResponseRedirect
from django.conf import settings
from re import compile

EXEMPT_URLS = [compile(settings.LOGIN_URL.lstrip('/'))]
if hasattr(settings, 'LOGIN_EXEMPT_URLS'):
    EXEMPT_URLS += [compile(expr) for expr in settings.LOGIN_EXEMPT_URLS]


class LoginRequiredMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        if request.user:
            if not request.user.is_authenticated():
                path = request.path_info.lstrip('/')
                if not any(m.match(path) for m in EXEMPT_URLS):
                    return HttpResponseRedirect(settings.LOGIN_URL)
        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
