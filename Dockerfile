# Prepare the base environment.
FROM ubuntu:22.04 as builder_base_pbs
MAINTAINER asi@dbca.wa.gov.au
ENV DEBIAN_FRONTEND=noninteractive
ENV SECRET_KEY="ThisisNotRealKey"
ENV USER_SSO="Docker Build"
ENV PASS_SSO="ThisIsNotReal"
ENV EMAIL_HOST="localhost"
ENV FROM_EMAIL="no-reply@dbca.wa.gov.au"
ENV KMI_DOWNLOAD_URL="https://localhost/"
ENV CSV_DOWNLOAD_URL="https://localhost/"
ENV SHP_DOWNLOAD_URL="https://localhost/"
ENV DATABASE_URL="sqlite://memory"

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -yq git mercurial gcc gdal-bin libsasl2-dev libpq-dev
RUN apt-get install -y python3-setuptools python3-dev python3-pip
RUN apt-get install -y fex-utils imagemagick poppler-utils
RUN apt-get install -y libldap2-dev libssl-dev wget build-essential vim virtualenv libmagic-dev texlive-full
# RUN ln -s /usr/bin/python3 /usr/bin/python

RUN groupadd -g 5000 oim 
RUN useradd -g 5000 -u 5000 oim -s /bin/bash -d /app
RUN mkdir /app 
RUN chown -R oim.oim /app 

RUN wget https://raw.githubusercontent.com/dbca-wa/wagov_utils/main/wagov_utils/bin/default_script_installer.sh -O /tmp/default_script_installer.sh
RUN chmod 755 /tmp/default_script_installer.sh
RUN /tmp/default_script_installer.sh

COPY binaries/ffsend /usr/local/bin/

# Install Python libs from requirements.txt.
FROM builder_base_pbs as python_libs_pbs
WORKDIR /app
USER oim
RUN virtualenv /app/venv
ENV PATH=/app/venv/bin:$PATH
RUN git config --global --add safe.directory /app

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt 
  # Update the Django <1.11 bug in django/contrib/gis/geos/libgeos.py
  # Reference: https://stackoverflow.com/questions/18643998/geodjango-geosexception-error
  #&& sed -i -e "s/ver = geos_version().decode()/ver = geos_version().decode().split(' ')[0]/" /usr/local/lib/python2.7/dist-packages/django/contrib/gis/geos/libgeos.py \
  # Update policy map for Imagemagick (allow it read access to PDFs).
  #&& sed -i -e 's/policy domain="coder" rights="none" pattern="PDF"/policy domain="coder" rights="read|write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml \
  #&& rm -rf /var/lib/{apt,dpkg,cache,log}/ /tmp/* /var/tmp/*
# Copy the ffsend prebuilt binary.

# Install the project.
FROM python_libs_pbs
COPY gunicorn.ini manage.py ./
COPY fex.id /app/.fex/id
COPY .git ./.git
#RUN git log --pretty=medium -30 > ./git_history_recent && rm -rf .git
COPY pbs ./pbs
COPY pbs_project ./pbs_project
COPY smart_selects ./smart_selects
COPY swingers ./swingers
COPY templates ./templates
COPY startup.sh /startup.sh

#COPY .env ./.env
RUN touch .env
#RUN python3 manage.py migrate
RUN python3 manage.py collectstatic --noinput
RUN rm .env

# Health checks for kubernetes 
#RUN wget https://raw.githubusercontent.com/dbca-wa/wagov_utils/main/wagov_utils/bin/health_check.sh -O /bin/health_check.sh
#RUN chmod 755 /bin/health_check.sh

# Run the application as the www-data user.
#USER www-data
HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]
EXPOSE 8080
# CMD ["gunicorn", "pbs_project.wsgi", "--config", "gunicorn.ini"]
CMD ["/startup.sh"]

