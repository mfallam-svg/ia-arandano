# Procfile para Render / Heroku - arranca la app con gunicorn
# Render expondrá la aplicación usando la variable de entorno $PORT
web: gunicorn run:app --workers 2 --bind 0.0.0.0:$PORT