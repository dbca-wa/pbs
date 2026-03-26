import os
import mimetypes
import subprocess
from PIL import Image

from collections import namedtuple

FileInfo = namedtuple('FileInfo', ['format', 'width', 'height', 'units'])


def get_dimensions(path, format='PDF', width=0, height=0, units='pt'):
    """
    Takes a document path and tests to see if it can extract dimensions from
    the document itself. Will return default width and height on failure.
    """
    #import ipdb; ipdb.set_trace()
    if os.path.exists(path):
        mime_type, _ = mimetypes.guess_type(path)
        if mime_type == 'application/pdf':
            # Handle PDFs differently to images. There may be multiple pages
            # but just use the first to get the dimensions.
            # identify reliably interprets rotation
            #width, height = subprocess.check_output([
            #    "identify", "-format", "%Wx%H,", path
            #]).split(",")[0].strip().split("x")
            # NOTE: The above command was not handling an execption by Imagemagick that returned the document dimension
            # plus an error message. The additional steps below are to handle this edge case as well as normal operation.
            try:
                out = subprocess.check_output(["identify", "-format", "%Wx%H,", path]).strip()
                out = out.split('\n')
                first = out[-1].strip().split(',')[0]
                width, height = first.split('x')
                width = int(width)
                height = int(height)
            except:
                output = subprocess.check_output(["pdfinfo", path]).decode("utf-8")
                for line in output.splitlines():
                    if line.startswith("Page size:"):
                        dimensions = line.split(":")[1].strip().split("x")
                        break
                width, height = dimensions[0].strip(), dimensions[1].split()[0].strip()
                width = int(float(width))
                height = int(float(height))
                #pass
        else:
            # Try to open the image and extract its properties
            try:
                image = Image.open(path)
            except IOError:
                pass
            else:
                format = image.format
                # image.size is a tuple of (width, height)
                width = image.size[0]
                height = image.size[1]
                units = 'px'
    return FileInfo(format, width, height, units)
