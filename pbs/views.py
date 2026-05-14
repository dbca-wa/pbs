from django.template import Context, loader
from django.http import HttpResponseServerError, HttpResponse
from django.shortcuts import redirect

import logging
import sys
import os
import mimetypes

from pbs_project import settings

log = logging.getLogger(__name__)


def handler500(request):
    context = {'request': request}
    t = loader.get_template('500.html')
    return HttpResponseServerError(t.render(Context(context)))

def sso_logout(request):
    return redirect('/sso/auth_logout')

def is_authorised_to_access_document(request):
    
    if request.user.is_active:
        return True
    else:
        return False

def getPrivateFile(request):
    if is_authorised_to_access_document(request):
        file_name_path =  request.path
        #norm path will convert any traversal or repeat / in to its normalised form
        full_file_path= os.path.normpath(settings.BASE_DIR+file_name_path) 
        #we then ensure the normalised path is within the BASE_DIR (and the file exists)
        if full_file_path.startswith(settings.BASE_DIR) and os.path.isfile(full_file_path):
            extension = file_name_path.split(".")[-1]
            the_file = open(full_file_path, 'rb')
            the_data = the_file.read()
            the_file.close()
            if extension == 'msg':
                return HttpResponse(the_data, content_type="application/vnd.ms-outlook")
            if extension == 'eml':
                return HttpResponse(the_data, content_type="application/vnd.ms-outlook")

            mimetypes.types_map.update({'.prj': 'application/octet-stream'})
            return HttpResponse(the_data, content_type=mimetypes.types_map['.'+str(extension.lower())])
       
    return HttpResponse()