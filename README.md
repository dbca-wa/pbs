# Prescribed Burn System

The Prescribed Burn System is used by officers within the Department of Parks & Wildlife (DPaW)
to generate and manage electronic Prescribed Fire Plans (ePFP).

Troubleshooting and support page on Confluence:
[PBS application support](https://confluence.dpaw.wa.gov.au/display/PBS/PBS+application+support)

# Installation

mkdir projects
cd projects/
git clone https://github.com/dbca-wa/pbs.git
cd pbs/
pwd
    /home/patrickm/projects/pbs
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt 

# Environment variables
cp /var/www/pbs/.env . (or create .env file) - [This project uses `django-confy` to set environment variables (in a `.env` file)]

	DEBUG=True
	DATABASE_URL="postgis://db_user:db_passwd@localhost/db_name"
	SECRET_KEY="my_secret_key"
	KMI_DOWNLOAD_URL="http://kmi.dpaw.wa.gov.au/geoserver/public/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=public:todays_burns&outputFormat=application%2Fvnd.google-earth.kml%2Bxml&SRSNAME=EPSG:4283"
	CSV_DOWNLOAD_URL="http://kmi.dpaw.wa.gov.au/geoserver/public/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=public:todays_burns&outputFormat=csv&SRSNAME=EPSG:4283"
	SHP_DOWNLOAD_URL="http://kmi.dpaw.wa.gov.au/geoserver/public/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=public:todays_burns&outputFormat=SHAPE-ZIP&SRSNAME=EPSG:4283"
	USER_SSO='SSO_user'
	PASS_SSO='SSO_passwd'
	ENV_TYPE="dev"

Outgoing emails use `TemplateEmailBase` and are logged to `logs/email.log`,
including subjects and recipient addresses. Set `EMAIL_DELIVERY=off` to disable
delivery; it defaults to `on`. The existing `PRODUCTION_EMAIL` and
`NON_PROD_EMAIL` settings still control SMTP recipient routing, so logged
recipients may differ from the actual SMTP recipients in non-production. The email
helper supplies `System-Environment` but does not preserve `ITSystem-ID`.

# Manual Django module fix
vi /home/patrickm/projects/pbs/venv/local/lib/python2.7/site-packages/django/contrib/gis/geos/libgeos.py (version issue in Django - requires manual fix)
change line:
	ver = geos_version().decode()
to:
	ver = geos_version().decode().split()[0]

# The above DB can be created from existing, as follows:
sudo -u postgres pg_dump -Fc -c pbs_dev > ../tmp/pbs_dev_07Jan2020.pgdump
dropdb -U fire -h localhost pbs_dev_patrickm
createdb -U fire -h localhost -O fire pbs_dev_patrickm
sudo -u postgres pg_restore -v -d pbs_dev_patrickm ../tmp/pbs_dev_07Jan2020.pgdump 

# To test:
./manage.py runserver 0.0.0.0:8499

