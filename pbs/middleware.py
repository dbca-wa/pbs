from django import http
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from dbca_utils.middleware import SSOLoginMiddleware


# class SSOLoginMiddleware(object):
#     def __init__(self, get_response):
#        self.get_response = get_response

#     def __call__(self, request):
#        # Process the request before view
#        response = self.process_request(request)
#        if response:
#            return response
#        # Process the response after view
#        response = self.get_response(request)
#        return response
    

#     def process_request(self, request):
#         if request.path.startswith('/logout') and "HTTP_X_LOGOUT_URL" in request.META:
#             logout(request)
#             return http.HttpResponseRedirect(request.META["HTTP_X_LOGOUT_URL"])
#         if not request.user.is_authenticated() and "HTTP_REMOTE_USER" in request.META:
#             attributemap = {
#                 "username": "HTTP_REMOTE_USER",
#                 "last_name": "HTTP_X_LAST_NAME",
#                 "first_name": "HTTP_X_FIRST_NAME",
#                 "email": "HTTP_X_EMAIL",
#             }

#             # for key, value in attributemap.iteritems():
#             for key, value in attributemap.items():
#                 attributemap[key] = request.META[value]

#             # start -- username update to fix issues in SSS
#             email = attributemap['email']
#             email_split = email.split("@")
#             domain_name = email_split[1]
#             domain_name_split = domain_name.split(".")
#             domain_host = domain_name_split[0]
#             username = email_split[0]+"."+domain_host
#             username = username[0:30]          
#             attributemap['username'] = username
#             # end -- username update to fix issues in SSS                
                
                
#             if hasattr(settings, "ALLOWED_EMAIL_SUFFIXES") and settings.ALLOWED_EMAIL_SUFFIXES:
#                 allowed = settings.ALLOWED_EMAIL_SUFFIXES
#                 # if isinstance(settings.ALLOWED_EMAIL_SUFFIXES, basestring):
#                 if isinstance(settings.ALLOWED_EMAIL_SUFFIXES, str):
#                     allowed = [settings.ALLOWED_EMAIL_SUFFIXES]
#                 if not any([attributemap["email"].lower().endswith(x) for x in allowed]):
#                     return http.HttpResponseForbidden()

#             if User.objects.filter(email__istartswith=attributemap["email"]).exists():
#                 user = User.objects.get(email__istartswith=attributemap["email"])
#             elif User.objects.filter(username__iexact=attributemap["username"]).exists():
#                 user = User.objects.get(username__iexact=attributemap["username"])
#             else:
#                 user = User()
#             #user.__dict__.update(attributemap)
#             for attr, value in attributemap.items():
#                setattr(user, attr, value)
#             user.save()
#             user.backend = 'django.contrib.auth.backends.ModelBackend'
#             login(request, user)


class PBSV2SSOLoginMiddleware(SSOLoginMiddleware):
    """Overide the SSOLoginMiddleware to set or delete the session variablers that
    are required by webtemplate_dbca. TODO: Remove this once Jason has updated
    the dbca_utils SSOLoginMiddleware."""

    def process_request(self, request):
        if request.path.startswith("/logout"):
            del request.session["is_authenticated"]
            del request.session["user_obj"]

        super().process_request(request)

        if request.user.is_authenticated:
            request.session["is_authenticated"] = True
            user_obj = {
                "user_id": request.user.id,
                "email": request.user.email,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "is_staff": request.user.is_staff,
            }
            request.session["user_obj"] = user_obj