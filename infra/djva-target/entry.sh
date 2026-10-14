redis-server --daemonize yes
python manage.py makemigrations system
python manage.py migrate --noinput
python manage.py loaddata db.json
gunicorn server.wsgi:application -w 4 -k gthread -b 0.0.0.0:80
