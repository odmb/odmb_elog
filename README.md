Commands to setup website
```
source set_env.sh
python3 manage.py migrate --run-syncd
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py createsuperuser
```

Commands to start server
```
python3 manage.py runserver
```

Connect to the below websites
localhost:8000  
localhost:8000/admin   

Use admin site to create baord types and baord locations.
