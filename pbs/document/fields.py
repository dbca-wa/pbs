import os
import shutil
import subprocess

from django.forms import ValidationError
from django.db.models import FileField
from django.template.defaultfilters import filesizeformat

from io import BytesIO
import tempfile
# from south.modelsinspector import add_introspection_rules


class ContentTypeRestrictedFileField(FileField):
    """
    Extend the Django FileField to specify:
    content_types - list containing allowed MIME types for upload.
    Example: ['application/pdf', 'image/jpeg']
    max_upload_size - a number indicating the maximum file size
                      (bytes) allowed for upload.
    Also convert to pdf
    """
    def __init__(self, content_types=None, max_upload_size=None,
                 *args, **kwargs):
        self.content_types = content_types
        self.max_upload_size = max_upload_size
        super(ContentTypeRestrictedFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(ContentTypeRestrictedFileField, self).clean(*args,
                                                                 **kwargs)
        upload = data.file
        content_type = upload.content_type
        fname = os.path.basename(data.path)
        workdir = tempfile.mkdtemp()
        zip_types = ['application/zip', 'application/x-zip-compressed']
        # with open(os.path.join(workdir, fname), "w") as fin:
        with open(os.path.join(workdir, fname), "wb") as fin:
            fin.write(data.read())
        if ((content_type in self.content_types and
             content_type not in zip_types)):
            if self.max_upload_size and upload._size > self.max_upload_size:
                raise ValidationError('Please ensure filesize is under %s. '
                                      'Current filesize: %s' % (
                                      filesizeformat(self.max_upload_size),
                                      filesizeformat(upload._size)))
            if fname.rsplit(".")[1] != "pdf":
                try:
                    pdfname = fname.rsplit(".")[0] + ".pdf"
                    subprocess.check_output(["convert", os.path.join(workdir, fname), os.path.join(workdir, pdfname)])
                    fname = pdfname
                except subprocess.CalledProcessError:
                    raise ValidationError("File {} appears to be corrupt, "
                                          "please check and try again.".format(fname))
            try:
                subprocess.check_output(["pdfinfo", "-box", os.path.join(workdir, fname)])
            except subprocess.CalledProcessError:
                raise ValidationError("File {0} appears to be corrupt, please "
                                      "check and try again.".format(fname))
            # data.file = BytesIO(open(os.path.join(workdir, fname), "r").read())
            data.file = BytesIO(open(os.path.join(workdir, fname), "rb").read())
            data.file.size = os.path.getsize(os.path.join(workdir, fname))
            shutil.rmtree(workdir)
        elif content_type not in zip_types:
            # Generate list of OK file extensions.
            ext = [i.split('/')[1] for i in self.content_types]
            raise ValidationError('Filetype not supported (acceptable types: '
                                  '{0})'.format(', '.join(ext)))
        return data

# add_introspection_rules(
#     [], ["^pbs\.document\.models\.ContentTypeRestrictedFileField"])
