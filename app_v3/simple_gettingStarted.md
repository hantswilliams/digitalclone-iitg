- Run docker (redis and minIO)
- Run frontend (5001) (PORT=5001 python app_v3/backend/app.py)
- Run celery worker (app_v3/backend/run_celery.py)
- Run frontend (3001) (PORT=3001 npm start)