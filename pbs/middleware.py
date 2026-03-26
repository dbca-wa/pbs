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

class PrescriptionCheckMiddleware(object):

    def __init__(self, get_response):            
            self.get_response = get_response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Run before executing any function code

        
        if request.path.startswith("/prescription/prescription"):
            request_path=request.path                                       
            request_path_obj=request_path.split('/')
            print('request_path_obj', request_path_obj[3])      
            # response = HttpResponse("<script> window.location='"+url_redirect+"';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"+url_redirect+"'> Redirecting please wait: "+url_redirect+"</a><div></div></center>")
            # return response          

        else:
               if request.path.startswith("/ledger-api/process-payment"):
                    # booking as expired or session been removed
                    url_redirect = reverse('public_make_booking')
                    response = HttpResponse("<script> window.location='"+url_redirect+"';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"+url_redirect+"'> Redirecting please wait: "+url_redirect+"</a><div></div></center>")
                    return response             
        return None

    def __call__(self, request):            
            # Run after executing any function code
            return self.pr(request)

    def pr(self, request):
        response= self.get_response(request)
        # if request.path.startswith('/static') or request.path.startswith('/favicon') or request.path.startswith('/media') or request.path.startswith('/api') or request.path.startswith('/search-availability/information/') or request.path.startswith('/search-availability/campground/') or request.path.startswith('/campground-image') or request.path == '/':
        #      pass
        # else:
        #     if 'ps_booking' in request.session:
        #         try:
        #             booking = Booking.objects.get(pk=request.session['ps_booking'])
        #         except:
        #             # no idea what object is in self.request.session['ps_booking'], ditch it
        #             del request.session['ps_booking']
        #             return response
        #         #if booking.booking_type != 3:
        #         #    # booking in the session is not a temporary type, ditch it
        #         #    del request.session['ps_booking']
        #         if booking.expiry_time is not None:
        #             if timezone.now() > booking.expiry_time and booking.booking_type == 3:
        #             # expiry time has been hit, destroy the Booking then ditch it
        #             #booking.delete()
        #                 del request.session['ps_booking']

        #         if request.path.startswith("/ledger-api/process-payment") or request.path.startswith('/ledger-api/payment-details'):      
                    
        #             if "ps_booking" not in request.session:
        #                  url_redirect = reverse('public_make_booking')
        #                  response = HttpResponse("<script> window.location='"+url_redirect+"';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"+url_redirect+"'> Redirecting please wait: "+url_redirect+"</a><div></div></center>")
        #                  return response    

        #             checkouthash =  hashlib.sha256(str(request.session["ps_booking"]).encode('utf-8')).hexdigest() 

        #             checkouthash_cookie = request.COOKIES.get('checkouthash')
        #             total_booking = Booking.objects.filter(pk=request.session['ps_booking']).count()
        #             if checkouthash_cookie != checkouthash or total_booking == 0:                         
        #                  # messages.error(request, "There was a booking mismatch issue while trying to complete your booking, your inprogress booking has been cancelled and will need to be completed again.  This can sometimes be caused by using multiple browser tabs and recommend only to complete a booking using one browser tab window. ")          
        #                  # return HttpResponseRedirect("/")  
        #                  url_redirect = reverse('public_make_booking')
        #                  response = HttpResponse("<script> window.location='"+url_redirect+"';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"+url_redirect+"'> Redirecting please wait: "+url_redirect+"</a><div></div></center>")
        #                  return response                                                                                                 

        #         if CHECKOUT_PATH.match(request.path) and request.method == 'POST' and booking.booking_type == 3:
        #             # safeguard against e.g. part 1 of the multipart checkout confirmation process passing, then part 2 timing out.
        #             # on POST boosts remaining time to at least 2 minutes
        #             booking.expiry_time = max(booking.expiry_time, timezone.now()+datetime.timedelta(minutes=2))
        #             booking.save()
        #     else:
        #          if request.path.startswith("/ledger-api/process-payment"):
        #             # booking as expired or session been removed
        #             url_redirect = reverse('public_make_booking')
        #             response = HttpResponse("<script> window.location='"+url_redirect+"';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"+url_redirect+"'> Redirecting please wait: "+url_redirect+"</a><div></div></center>")
        #             return response

        #     # force a redirect if in the checkout
        #     if ('ps_booking_internal' not in request.COOKIES) and CHECKOUT_PATH.match(request.path):
        #         if ('ps_booking' not in request.session) and CHECKOUT_PATH.match(request.path):
        #             url_redirect = reverse('public_make_booking')
        #             response = HttpResponse("<script> window.location='"+url_redirect+"';</script> <center><div class='container'><div class='alert alert-primary' role='alert'><a href='"+url_redirect+"'> Redirecting please wait: "+url_redirect+"</a><div></div></center>")
        #             return response
        #             #return HttpResponseRedirect(reverse('public_make_booking'))
        #         else:
        #             return response
        return response
