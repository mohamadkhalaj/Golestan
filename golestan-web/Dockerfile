FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SECRET_KEY ""
ENV WEB_CONCURRENCY 4
ENV DATABASE_URL "postgres://postgres:postgres@db:5432/golestan"
ENV PYTHONHASHSEED random
ENV DJANGO_DEBUG False
ENV DJANGO_ALLOWED_HOSTS "localhost,127.0.0.1"
RUN mkdir /golestan-web
COPY ./requirements.txt /golestan-web/

WORKDIR /golestan-web

RUN pip install --upgrade pip
RUN pip install -r requirements.txt