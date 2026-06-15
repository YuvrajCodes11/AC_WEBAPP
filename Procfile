release: python manage.py migrate --noinput && python manage.py seed_store_items
web: python manage.py migrate --noinput && python manage.py seed_store_items && gunicorn puriaccooling.wsgi --bind 0.0.0.0:$PORT
