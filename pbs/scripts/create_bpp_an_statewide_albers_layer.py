import os
import sys

import confy
from django.core.wsgi import get_wsgi_application


LAYER_NAME = 'BPP_AN_Statewide_Albers'
CATALOGUE_ENTRY_ID = 1210


def configure_django():
    proj_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if proj_path not in sys.path:
        sys.path.append(proj_path)
    os.chdir(proj_path)

    dot_env = os.path.join(proj_path, '.env')
    if os.path.exists(dot_env):
        confy.read_environment_file()

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pbs_project.settings')
    get_wsgi_application()


def ensure_layer():
    from pbs.review.models import Layer

    layer, created = Layer.objects.get_or_create(
        name=LAYER_NAME,
        defaults={
            'catalogue_entry_id': CATALOGUE_ENTRY_ID,
            'active': True,
        },
    )

    if created:
        print(
            'Layer created: name={0}, catalogue_entry_id={1}, active={2}'.format(
                layer.name,
                layer.catalogue_entry_id,
                layer.active,
            )
        )
        return

    print(
        'Layer already exists: name={0}, catalogue_entry_id={1}, active={2}'.format(
            layer.name,
            layer.catalogue_entry_id,
            layer.active,
        )
    )


if __name__ == '__main__':
    configure_django()
    ensure_layer()
