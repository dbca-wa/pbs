import os
import sys

import confy
from django.core.wsgi import get_wsgi_application


def configure_django():
    proj_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if proj_path not in sys.path:
        sys.path.append(proj_path)
    os.chdir(proj_path)

    dot_env = os.path.join(proj_path, '.env')
    if os.path.exists(dot_env):
        confy.read_environment_file()

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pbs_project.settings')

    application = get_wsgi_application()


def ensure_groups():
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    from pbs.prescription.models import JobQueue

    override_group, override_created = Group.objects.get_or_create(
        name='Override Application Administrator'
    )

    job_queue_group, job_queue_created = Group.objects.get_or_create(
        name='Job Queue Administrator'
    )

    content_type = ContentType.objects.get_for_model(JobQueue)
    permissions = Permission.objects.filter(
        content_type=content_type,
        codename__in=['view_jobqueue', 'change_jobqueue']
    )
    job_queue_group.permissions.add(*permissions)

    print(
        'Override Application Administrator: {0}'.format(
            'created' if override_created else 'already exists'
        )
    )
    print(
        'Job Queue Administrator: {0}'.format(
            'created' if job_queue_created else 'already exists'
        )
    )
    print(
        'Assigned JobQueue permissions: {0}'.format(
            ', '.join(sorted(permission.codename for permission in permissions))
        )
    )


if __name__ == '__main__':
    configure_django()
    ensure_groups()