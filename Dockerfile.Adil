FROM --platform=linux/amd64 python:3.10.5

LABEL \
  maintainer="Adil Rashitov <adil@wastelabs.co>" \
  org.opencontainers.image.title="sport_event_planning_platform" \
  org.opencontainers.image.description="Dockerfile of veolia frontend" \
  org.opencontainers.image.authors="Adil Rashitov <adil@wastelabs.co>" \
  org.opencontainers.image.url="https://github.com/AtmosOne/dev_veolia_uk_frontend"

WORKDIR /dev_veolia_uk_frontend


ENV POETRY_VIRTUALENVS_CREATE=false


COPY ./ ./

RUN pip3 install --upgrade pip \
	&& pip3 install wheel \
	&& pip3 install poetry==1.3.1 \
	&& poetry install

# EXPOSE 0000
