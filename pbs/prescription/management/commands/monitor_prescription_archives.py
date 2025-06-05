"""
    The WHY:
        There is a known issue in the PBS system where the creation of a .pdf archive file can fail to occur.
        It should occur every time a prescription status is changed, but sometimes it doesn't.
        This script is designed to run once a day and do a series of checks for each prescription in the system.

    What it does:
        It will check if the archive directory exists, if not it will log an issue.
        If the archive directory does exist, it will then check if there is an archive file for each status field
        that has been modified.
        Issues are ordered by date modified descending, stored as rows in a .csv file and sent via email to the
        address(es) specied in the FIRE_NOTIFICATION_EMAIL environment variable.
        If the environment variable is not set then the issues are logged to the console instead (which would end up in 
        the container logs in rancher/k8s)

    Limitations:
        The script only checks the most recent status change for each status field.
        There is no way to know the exact order that statuses were changed in for previous status changes
        so we can't check for every status change, only the most recent one.
"""
import csv
import logging
import os
import re

from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.formats import localize

from pbs.prescription.models import Prescription

logger = logging.getLogger("pbs")


class Command(BaseCommand):
    help = "A command to ensure users are aware of any prescription archives that failed to generate"
    DATE = localize(timezone.localtime(timezone.now()).date())

    def handle(self, *args, **options):
        issues = []
        for prescription in Prescription.objects.all().order_by("-modified"):
            has_status_been_modified = (
                prescription.planning_status_modified or
                prescription.endorsement_status_modified or
                prescription.approval_status_modified or
                prescription.ignition_status_modified or
                prescription.status_modified
            )

            if not has_status_been_modified:
                continue

            if not self.check_archive_directory(prescription, issues):
                continue

            self.check_archive_files(prescription, issues)

        if not issues:
            logger.debug("No prescription archive issues found today ({})".format(self.DATE))
            return
        
        issues_csv = self.generate_issues_csv(issues)
        self.send_monitoring_email(issues, issues_csv)


    def check_archive_directory(self, prescription, issues):
        archive_directory = os.path.join(settings.MEDIA_ROOT, "snapshots", prescription.financial_year.replace("/","-"), prescription.burn_id)
        exists = True
        if not os.path.exists(archive_directory):
            issue = "No archive directory found at: {}".format(archive_directory)
            issues.append({"prescription":prescription.burn_id, "issue": issue, "modified":timezone.localtime(prescription.modified)})
            exists = False
        if exists:
            logger.debug("Archive directory exists: {}".format(exists))
        return exists

    def check_archive_files(self, prescription, issues):
        logger.debug("Checking archive files for prescription: {}".format(prescription.burn_id))
        status_fields = [
            "planning_status",
            "endorsement_status",
            "approval_status",
            "ignition_status",
            "status"
        ]
        for field in status_fields:
            logger.debug("Checking archive file for field: {}".format(field))
            if not getattr(prescription, field + "_modified", None):
                continue

            logger.debug("Status field '{}' last modified {}".format(field, getattr(prescription, field + "_modified", None)))

            # We now know this status field has changed at least once so can check if there is an
            # archive file for it
            self.check_archive_file(prescription, field, issues)

    def check_archive_file(self, prescription, field, issues):
        archive_file_path = os.path.join(settings.MEDIA_ROOT, "snapshots", prescription.financial_year.replace("/","-"), prescription.burn_id)
        exists = False
        status_display_method = getattr(prescription, "get_" + field + "_display")
        status_display = status_display_method()
        status_display_hyphenated = status_display.lower().replace(" ","-")
        for file in os.listdir(archive_file_path):
            logger.debug("{}".format(file))
            pattern = r"{}_{}_.*{}.*\.pdf".format(prescription.burn_id, field, status_display_hyphenated)
            logger.debug(pattern)
            if re.search(pattern, file):
                return True

        if not exists:
            issue = "No archive file found for status change for field '{}' to value '{}'".format(field, status_display)
            logger.debug(issue + "\n\n")
            issues.append({"prescription":prescription.burn_id, "issue": issue, "modified":timezone.localtime(prescription.modified)})

        return exists

    def generate_issues_csv(self, issues):
        csv_path = settings.MEDIA_ROOT + "/prescription-archive-issues/"
        if not os.path.exists(csv_path):
            os.makedirs(csv_path)
        with open(csv_path + "prescription-archive-issues-{}.csv".format(self.DATE), "w") as file:
            writer = csv.writer(file)
            field = ["Prescription", "Issue", "Date Last Modified"]
            writer.writerow(field)
            for issue in issues:
                writer.writerow([issue["prescription"], issue["issue"], issue["modified"]])
        return file

    def send_monitoring_email(self, issues, issues_csv):
        subject = "PBS - Prescription Archive Monitoring Notification Email - {}".format(self.DATE)
        body = ("The following prescriptions have one or more archiving issue:\n\n")
        body += ", ".join([p["prescription"] for p in issues])
        body += "\n\nSee the attached .csv file for more information about each issue."

        if not settings.FIRE_NOTIFICATION_EMAIL:
            # If there is no address to send the email to then write the data to the log instead
            self.log_issues(body, issues_csv)
            return

        try:
            with open(issues_csv.name, "r") as file:
                mail = EmailMessage(subject=subject, body=body, from_email=settings.FEX_MAIL, to=settings.FIRE_NOTIFICATION_EMAIL.split(","))
                mail.attach(file.name, file.read(), "text/csv")
                mail.send()
        except (SMTPException, IOError) as e:
            logger.exception("Failed to send Prescription Archive Monitoring Notification Email: \n{}".format(e))
            # If email sending fails then write the data to the log instead
            self.log_issues(body, issues_csv)
            
    def log_issues(self, body, issues_csv):
            logger.warning("ENV FIRE_NOTIFICATION_EMAIL is not set. Unable to send notification email.")
            logger.warning(body)
            with open(issues_csv.name, "r") as file:
                csvFile = csv.reader(file)
                for line in csvFile:
                    logger.warning(line)
