from django.template import Context, loader
from django.http import HttpResponseServerError, HttpResponse
from django.shortcuts import redirect
from django.utils import timezone

import logging
import sys
import os
import mimetypes

from pbs_project import settings
from pbs.models import FileDownloadHash

log = logging.getLogger(__name__)


def _download_link_expired_response(status=410):
    html = (
        '<html><head><title>Download Link Expired</title></head>'
        '<body>'
        '<h2>Download link expired</h2>'
        '<p>The download file link has expired. Please generate a new PDF download link.</p>'
        '</body></html>'
    )
    return HttpResponse(html, content_type='text/html', status=status)


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
        if request.path.startswith('/private-media/download/'):
            token = request.path[len('/private-media/download/'):].strip('/').strip()
            if token:
                download_link = FileDownloadHash.objects.filter(token=token).first()
                if download_link:
                    if download_link.expires_at <= timezone.now():
                        download_link.delete()
                        return _download_link_expired_response(status=410)

                    full_file_path = os.path.normpath(download_link.file_path)
                    if full_file_path.startswith(settings.PRIVATE_MEDIA_ROOT) and os.path.isfile(full_file_path):
                        extension = full_file_path.split('.')[-1]
                        with open(full_file_path, 'rb') as the_file:
                            the_data = the_file.read()
                        if extension == 'msg':
                            return HttpResponse(the_data, content_type='application/vnd.ms-outlook')
                        if extension == 'eml':
                            return HttpResponse(the_data, content_type='application/vnd.ms-outlook')

                        mimetypes.types_map.update({'.prj': 'application/octet-stream'})
                        return HttpResponse(the_data, content_type=mimetypes.types_map['.' + str(extension.lower())])
            return _download_link_expired_response(status=410)

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