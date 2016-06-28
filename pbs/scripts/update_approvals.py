import os
import sys
import confy
from django.core.wsgi import get_wsgi_application
try:
    confy.read_environment_file('.env')
except:
    print('ERROR: Script must be runs from PROJECT BASE_DIR')
    exit()

application = get_wsgi_application() # This is so models get loaded.

proj_path = os.getcwd()
sys.path.append(proj_path)
os.chdir(proj_path)

# ----------------------------------------------------------------------------------------
# Script starts here
# ----------------------------------------------------------------------------------------

import csv
from datetime import datetime, date
import pytz
from pbs.prescription.models import Prescription

def read_ids(filename):
    return [i[0] for i in list(csv.reader(open(filename), delimiter=',', quotechar='"'))]

def update_currently_approved(ids):
    count = 0
    for p in Prescription.objects.filter(burn_id__in=ids):
        p.financial_year = '2016/2017'
        p.planning_status_modified = datetime(2016, 6, 27, tzinfo=pytz.UTC)
        p.save()
        count += 1
    print 'Updated Currently Approved season and approved date for {} ePFPs'.format(count)

def update_seeking_approval(ids):
    count = 0
    for p in Prescription.objects.filter(burn_id__in=ids):
        p.planning_status = 3
        p.planning_status_modified = datetime(2016, 6, 27, tzinfo=pytz.UTC)
        p.save()
        count += 1
    print 'Updated Seeking Approval status from DRAFT to APPROVED and Approval Date for {} ePFPs'.format(count)

def update_season(ids):
    count = 0
    for p in Prescription.objects.filter(burn_id__in=ids):
        p.financial_year = '2016/2017'
        p.save()
        count += 1
    print 'Updated Seeking Approval status from DRAFT to APPROVED for {} ePFPs'.format(count)


if __name__ == "__main__":
    cur_approved_ids = read_ids('pbs/scripts/currently_approved.txt')
    update_currently_approved(cur_approved_ids)
    #print cur_approved_ids, len(cur_approved_ids)

    seeking_approval_ids = read_ids('pbs/scripts/seeking_approval.txt')
    update_seeking_approval(seeking_approval_ids)

    update_season_ids = read_ids('pbs/scripts/update_season.txt')
    update_season(update_season_ids)

