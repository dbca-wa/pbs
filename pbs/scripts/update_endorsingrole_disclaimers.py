import argparse
import os
import sys

import confy
from django.core.wsgi import get_wsgi_application
from django.db import transaction


proj_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if proj_path not in sys.path:
    sys.path.append(proj_path)
os.chdir(proj_path)

dot_env = os.path.join(proj_path, '.env')
if os.path.exists(dot_env):
    confy.read_environment_file()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pbs_project.settings')

application = get_wsgi_application()


from pbs.prescription.models import EndorsingRole  # noqa: E402


def update_disclaimers(old_text='DPaW', new_text='department', dry_run=False):
    updated = 0
    roles = EndorsingRole.objects.filter(disclaimer__contains=old_text).order_by('index')

    with transaction.atomic():
        for role in roles:
            old_disclaimer = role.disclaimer
            new_disclaimer = old_disclaimer.replace(old_text, new_text)

            if old_disclaimer == new_disclaimer:
                continue

            updated += 1
            print('Updating #{0} {1}'.format(role.pk, role.name))
            print('  OLD: {0}'.format(old_disclaimer))
            print('  NEW: {0}'.format(new_disclaimer))

            if not dry_run:
                role.disclaimer = new_disclaimer
                role.save(update_fields=['disclaimer'])

        if dry_run:
            transaction.set_rollback(True)

    action = 'would be updated' if dry_run else 'updated'
    print('{0} EndorsingRole record(s) {1}.'.format(updated, action))


def main():
    parser = argparse.ArgumentParser(
        description='Replace text in EndorsingRole disclaimer records.'
    )
    parser.add_argument('--old', default='DPaW', help='Text to replace')
    parser.add_argument('--new', default='department', help='Replacement text')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show changes without saving them'
    )
    args = parser.parse_args()

    update_disclaimers(old_text=args.old, new_text=args.new, dry_run=args.dry_run)


if __name__ == '__main__':
    main()