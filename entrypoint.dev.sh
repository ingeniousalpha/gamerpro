#!/bin/sh
python manage.py collectstatic --noinput --clear
python manage.py migrate
gunicorn -c config/server/gunicorn.conf.py --reload