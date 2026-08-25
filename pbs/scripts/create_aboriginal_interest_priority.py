import os
import sys

import confy
from django.core.wsgi import get_wsgi_application

proj_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if proj_path not in sys.path:
    sys.path.append(proj_path)
os.chdir(proj_path)

dot_env = os.path.join(proj_path, '.env')
if os.path.exists(dot_env):
    confy.read_environment_file()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pbs_project.settings')

application = get_wsgi_application()

# ----------------------------------------------------------------------------------------
# Script starts here
# ----------------------------------------------------------------------------------------

from django.contrib.auth.models import User
from django.utils import timezone

from pbs.prescription.models import PriorityJustification, Purpose


PURPOSE_NAME = 'Aboriginal interest'
PRIORITY_ORDER = 8
ADMIN_USERNAME = 'admin'


def create_or_update_priority_justification():
    admin = User.objects.get(username=ADMIN_USERNAME)
    now = timezone.now()

    try:
        purpose = Purpose.objects.get(name=PURPOSE_NAME)
    except Purpose.DoesNotExist:
        print('Purpose not found, skipping: {}'.format(PURPOSE_NAME))
        return

    exists = PriorityJustification.objects.filter(
        purpose=purpose,
        prescription=None,
    ).exists()

    if exists:
        print(
            'PriorityJustification already exists for purpose="{}" and prescription=None. No action taken.'.format(
                purpose.name
            )
        )
        return

    priority_justification = PriorityJustification.objects.create(
        purpose=purpose,
        prescription=None,
        order=PRIORITY_ORDER,
        creator=admin,
        modifier=admin,
        created=now,
        modified=now,
        criteria=' - Facilitation and Protection of Aboriginal Interests\n    - Promotion of cultural land management and practices (Cultural Ecological Knowledge)\n    - Caring for Country\n    - Supporting customary activities\n    - Maintaining cultural knowledge systems\n - Protection or management of cultural and heritage sites and values\n    - Caring for songlines, sacred sites, ceremonial grounds, and places of historical importance\n    - Regenerate culturally significant species\n - Aboriginal led or co-designed\n - Supporting and strengthening cultural knowledge transfer and connection to Country\n - Joint and Co-operative Management arrangements   \n - Heal Country',
    )

    print('Purpose exists: {}'.format(purpose.name))
    print(
        'PriorityJustification created: id={}, purpose={}, prescription={}, order={}, creator={}, created={}, modified={}, criteria={}'.format(
            priority_justification.id,
            priority_justification.purpose.name,
            priority_justification.prescription,
            priority_justification.order,
            priority_justification.creator.username,
            priority_justification.created,
            priority_justification.modified,
            priority_justification.criteria,
        )
    )


if __name__ == '__main__':
    create_or_update_priority_justification()