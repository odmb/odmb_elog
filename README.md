Commands to setup website
```
git clone git@github.com:odmb/odmb_elog.git
cd odmb_elog
source set_env.sh
python3 manage.py makemigrations elog
python3 manage.py migrate
python3 manage.py createsuperuser
```

Commands to start server
```
python3 manage.py runserver 0.0.0.0:8000
```

Connect to the below websites  
localhost:8000  
localhost:8000/admin   

Use admin site to create board types and board locations.
