import tempfile
import traceback
import logging
import shutil
import humanize
import subprocess
import os
import time
import webbrowser

from django.utils import timezone
from django.conf import settings
from django.http import HttpResponse,HttpResponseRedirect
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib import messages

logger = logging.getLogger('pdf')

class PdflatexResult(object):
    def __init__(self,err_msg=None,template_file=None,pdf_file=None,log_file=None,directory=None):
        self.err_msg = err_msg
        self.template_file = template_file
        self.pdf_file = pdf_file
        self.log_file = log_file
        self.directory = directory
        self._filesize = None
        self._humanize_filesize = None

    def __enter__(self):
        return self

    def __exit__(self,exc_type, exc_value, traceback):
        #remote the temporary folder
        if self.directory:
            try:
                shutil.rmtree(self.directory)
            except :
                traceback.print_exc()

    @property
    def succeed(self):
        return True if self.pdf_file else False

    @property
    def template_generated_failed(self):
        return True if self.template_file is None else False

    @property
    def pdf_generated_failed(self):
        return True if self.pdf_file is None else False

    @property
    def filesize(self):
        if self._filesize is None:
            if self.pdf_file:
                self._filesize = os.path.getsize(self.pdf_file)
            else:
                self._filesize = 0  

        return self._filesize

    @property
    def errormessage(self):
        if self.err_msg:
            return self.err_msg
        elif self.log_file:
            with open(self.log_file,"r") as f:
                return f.read()
        else:
            return "Unknown excepiton."

    @property
    def humanize_filesize(self):
        if self._humanize_filesize is None:
            if self.filesize:
                self._humanize_filesize = humanize.naturalsize(self.filesize)
            else:
                self._humanize_filesize = ""

        return self._humanize_filesize

def pdflatex(prescription,template="pfp",downloadname=None,embed=True,headers=True,title="Prescribed Fire Plan",baseurl=None):
    #return PdflatexResult()   #DELETE AFTER TESTING
    logger = logging.getLogger('pdf_debugging')
    #for doc in prescription.document_set.all():
        
    logger.info("_________________________ START ____________________________")
    logger.info("Starting a PDF output for {}".format(prescription.burn_id))
    baseurl = baseurl or settings.BASE_URL

    texname = template + ".tex"
    filename = template + ".pdf"
    logfilename = template + ".log"
    now = timezone.localtime(timezone.now())
    if not downloadname:
        timestamp = now.isoformat().rsplit(".")[0].replace(":", "")
        downloadname = "{0}_{1}_{2}_{3}".format(prescription.season.replace('/', '-'), prescription.burn_id, timestamp, filename).replace(' ', '_')

    directory = None
    result = PdflatexResult()
    try:
        subtitles = {
            "parta": "Part A - Summary and Approval",
            "partb": "Part B - Burn Implementation Plan",
            "partc": "Part C - Burn Closure and Evaluation",
            "partd": "Part D - Supporting Documents and Maps"
        }
        context = {
            'current': prescription,
            'prescription': prescription,
            'embed': embed,
            'headers': headers,
            'title': title,
            'subtitle': subtitles.get(template, ""),
            'timestamp': now,
            'downloadname': downloadname,
            'settings': settings,
            'baseurl': baseurl
        }
         # Determine if this site is Dev/Test/UAT/Prod - if UAT or DEV then do not embed docs
        hostenv = settings.ENV_TYPE
        logger.info('ENV_TYPE: ' + hostenv)
        if hostenv.lower() in ['dev', 'uat']:
            context['embed'] = False
        
        err_msg = None
        try:
            output = render_to_string("latex/" + template + ".tex", context)
            logger.info("Output to render for {0} {1} successful.".format(prescription.burn_id, downloadname))
        except Exception as e:
            traceback.print_exc()
            err_msg = u"PDF tex template render failed (might be missing attachments)."
            #logger.exception("{0}\n{1}".format(err_msg,e))
            result.err_msg = "{0}\n\n{1}\n\n{2}".format(err_msg,e, traceback.format_exc())
            logger.info('PDF tex template render failed (might be missing attachments).')
            logger.info("Returning result. No PDF output for {0}\n{1}. Check the log file for more info.".format(prescription.burn_id, downloadname))
            return result

        directory = tempfile.mkdtemp(prefix="pbs_pdflatex")
        if not os.path.exists(directory):
            os.mkdir(directory)
        result.directory = directory
        texpath = os.path.join(directory, texname)
        with open(texpath, "w") as f:
            logger.info('Writing to {}'.format(texpath))
            # f.write(output.encode('utf-8'))
            f.write(output)
        result.template_file = texpath

        logger.info("Starting PDF rendering process ...")
        #cmd = ['latexmk', '-f', '-silent', '-pdf', '-outdir={}'.format(directory), texpath]
        # cmd = ['latexmk', '-f','-pdf', '-outdir={}'.format(directory), texpath]
        cmd = [
            'latexmk',
            '-f',
            #'-silent',
            '-pdf',
            '-outdir={}'.format(directory),
            '-interaction=nonstopmode',
            '-halt-on-error',
            '-file-line-error',  # Enables file and line number reporting
            texpath ]

        logger.info("Running: {0}".format(" ".join(cmd)))
        #subprocess.call(cmd)
        try:
            res = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            #print(res.stdout.decode())
        except subprocess.CalledProcessError as e:
            # print(f"Command '{cmd}' failed with return code {e.returncode}")
            logger.info("Command {0} failed with return code {1}".format(cmd, e.returncode))
            #print(f"Error output: {e.stderr.decode()}")
        
        logfile = os.path.join(directory, logfilename)
        if os.path.exists(logfile):
            result.log_file = logfile
            if not result.succeed:
                log_dir=os.path.join(settings.BASE_DIR, 'logs', 'pdf', prescription.burn_id, downloadname.replace('.pdf', ''))
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                    shutil.copytree(directory, log_dir, dirs_exist_ok=True)
                    copied_log_file= os.path.join(log_dir, logfilename)
                    result.log_file = copied_log_file
        pdffile = os.path.join(directory, filename)
        if os.path.exists(pdffile):
            result.pdf_file = pdffile
            logger.info("PDF output for {0} {1} successful".format(prescription.burn_id, downloadname)) 
        else:
            err_msg = u"PDF generation failed for "
            result.err_msg = "{0}\n\n{1}\n\n{2}".format(err_msg,prescription.burn_id,downloadname)
            logger.info("PDF generation failed after subprocess run for {} {}. Check the log file located at {} for errors ".format(prescription.burn_id, downloadname, result.log_file))            
        # logfile = os.path.join(directory, logfilename)
        # if os.path.exists(logfile):
        #     result.log_file = logfile
        #     if not result.succeed:
        #         log_dir=os.path.join(settings.BASE_DIR, 'logs', 'pdf', prescription.burn_id, downloadname.replace('.pdf', ''))
        #         if not os.path.exists(log_dir):
        #             os.makedirs(log_dir)
        #             shutil.copytree(directory, log_dir, dirs_exist_ok=True)
        #             copied_log_file= os.path.join(log_dir, logfilename)
        #             result.log_file = copied_log_file
        return result
    except Exception as e:
        traceback.print_exc()
        err_msg = u"PDF generated failed."
        #logger.exception("{0}\n{1}".format(err_msg,e))
        result.err_msg = "{0}\n\n{1}\n\n{2}".format(err_msg,e, traceback.format_exc())
        logger.info(err_msg)
        return result

def download_pdf(request, prescription):
    logger = logging.getLogger('pdf_debugging')
    logger.info('157: download_pdf called')
    template = request.GET.get("template", "pfp")
    embed = False if request.GET.get("embed","true").lower() == "false" else True
    title = request.GET.get("title", "Prescribed Fire Plan"),
    headers = False if request.GET.get("headers","true").lower() == "false" else True
    download = False if request.GET.get("download","false").lower() == "false" else True
    baseurl = request.build_absolute_uri("/")[:-1]
    filename = template + ".pdf"
    now = timezone.localtime(timezone.now())
    timestamp = now.isoformat().rsplit(".")[0].replace(":", "")
    downloadname = "{0}_{1}_{2}_{3}".format(prescription.season.replace('/', '-'), prescription.burn_id, timestamp, filename).replace(' ', '_')
    with pdflatex(prescription,template=template,downloadname=downloadname,embed=embed,headers=headers,title=title,baseurl=baseurl) as pdfresult:
        if pdfresult.succeed:
            if pdfresult.filesize / (1024 * 1024) >= 10:
                token = '_token_10'
            else:
                token = '_token'
            logger.info('Filesize: {}'.format(pdfresult.humanize_filesize))
            if settings.PDF_TO_FEXSRV:
                cmd = [
                    'ffsend',
                    'upload',
                    '--quiet',
                    '--incognito',
                    '--host', settings.SEND_URL,
                    '--download-limit', str(settings.SEND_DOWNLOAD_LIMIT),
                    '--force',
                    '--name', downloadname,
                    pdfresult.pdf_file
                ]
                logger.info('ffsend cmd: {}'.format(cmd))
                output = subprocess.check_output(cmd)
                file_url = output.decode('utf-8').strip()
                logger.info('Sending email notification to user of download URL')
                subject = 'Prescribed Burn System: file {}'.format(downloadname)
                email_from = settings.FEX_MAIL
                message = 'Prescribed Burn System: file {} can be downloaded at:\n\t{}\nFile size: {}\nNo. of times file can be downloaded: {}'.format(
                   downloadname, file_url, pdfresult.filesize, settings.SEND_DOWNLOAD_LIMIT)
                send_mail(subject, message, email_from, [request.user.email])
                url = request.META.get('HTTP_REFERER')  # redirect back to the current URL
                logger.info("__________________________ END _____________________________")
                resp = HttpResponseRedirect(url)
                resp.set_cookie('fileDownloadToken', token)
                resp.set_cookie('fileUrl', file_url)
                return resp
            else:
                # inline http response - pdf returned to web page
                response = HttpResponse(content_type='application/pdf')
                if download:
                    disposition = "attachment"
                else:
                    disposition = "inline"
                response['Content-Disposition'] = ('{0}; filename="{1}"'.format(disposition, downloadname))
                response.set_cookie('fileDownloadToken', token)
                logger.info("Reading PDF output from {}".format(pdfresult.pdf_file))
                with open(pdfresult.pdf_file,"rb") as f:
                    response.write(f.read())
                logger.info("Finally: returning PDF response.")
                logger.info("__________________________ END _____________________________")
                return response

        else:
            error_response = HttpResponse(content_type='text/html')
            errortxt = downloadname.replace(".pdf", ".errors.txt.html")
            error_response['Content-Disposition'] = '{0}; filename="{1}"'.format("inline", errortxt)
            error_response.write(pdfresult.errormessage)

            return error_response


