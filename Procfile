# Procfile para Render / Heroku - arranca la app con gunicorn
# Render expondrá la aplicación usando la variable de entorno $PORT
web: PYTHONPATH=src gunicorn web_app.app:app --workers 2 --bind 0.0.0.0:$PORT
