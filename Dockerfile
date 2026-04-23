# Prepare the base environment.
FROM ghcr.io/dbca-wa/docker-apps-dev:ubuntu_2510_base_python AS builder_base_pbs

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
RUN apt-get install -yq libsasl2-dev 
RUN apt-get install -y fex-utils imagemagick poppler-utils
RUN apt-get install -y libldap2-dev libssl-dev build-essential 
RUN apt-get install -y latexmk texlive-lang-english texlive-latex-recommended texlive-base texlive-latex-base texlive-fonts-recommended texlive-latex-extra
#texlive-full
# RUN apt-get install --no-install-recommends -y texlive-bibtex-extra texlive-binaries texlive-extra-utils texlive-fonts-extra texlive-formats-extra texlive-humanities texlive-latex-base texlive-latex-extra texlive-latex-recommended texlive-luatex texlive-metapost texlive-pictures texlive-plain-generic texlive-pstricks texlive-publishers texlive-science texlive-xetex
RUN apt-get install --no-install-recommends -y run-one

RUN groupadd -g 5000 oim 
RUN useradd -l -g 5000 -u 5000 oim -s /bin/bash -d /app
RUN mkdir /app 
RUN chown -R oim.oim /app

# Copy the ffsend prebuilt binary.
COPY binaries/ffsend /usr/local/bin/

RUN apt-get clean
RUN rm -rf /tmp/*
# Install Python libs from requirements.txt.
FROM builder_base_pbs as python_libs_pbs
WORKDIR /app
USER oim
RUN virtualenv /app/venv
ENV PATH=/app/venv/bin:$PATH
RUN git config --global --add safe.directory /app

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt 

# Install the project.
FROM python_libs_pbs
COPY gunicorn.ini manage.py ./
COPY fex.id /app/.fex/id
#COPY .git ./.git
#RUN git log --pretty=medium -30 > ./git_history_recent && rm -rf .git
COPY pbs ./pbs
COPY pbs_project ./pbs_project
COPY smart_selects ./smart_selects
COPY swingers ./swingers
COPY templates ./templates
COPY --chown=oim:oim  python-cron ./
COPY startup.sh /startup.sh
#COPY python-cron ./
RUN touch .env
RUN mkdir /app/logs
RUN python /app/manage.py collectstatic --noinput

HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]
EXPOSE 8080
CMD ["/startup.sh"]

