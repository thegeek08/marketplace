web: python manage.py collectstatic --noinput && python manage.py migrate && gunicorn marketplace.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
