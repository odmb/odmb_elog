#!/bin/bash
daemon(){

#This path is specific to this directory. This is true for the pushed code. 
#This should not be an issue in general unless we move the database. I (Anders) will try to fix this. Just unsure of the best path forward.
#Need to use base folder of the project
ODMB75_DB_PATH="/data/odmb75_database/odmb_elog"

echo "Set environment for database"
source "$ODMB75_DB_PATH/set_env.sh"

echo "Starting ODMB75 Database"
python3 "$ODMB75_DB_PATH/manage.py" runserver 0.0.0.0:8000
}

start(){

echo "PLEASE WORK"

echo "Call database daemon."
daemon &

echo "Add PID to /var/run/run_odmb75_database.pid"
PID=$!
echo $PID > /var/run/run_odmb75_database.pid

}


stop(){
echo "Killing database process in /var/run/run_odmb75_database.pid"
kill $(cat /var/run/run_odmb75_database.pid)
rm /var/run/run_odmb75_database.pid
}

restart(){
stop
start
}

now=$(date "+%m_%d_%y__%H_%M_%S")
"$@" > /data/odmb75_database/odmb_elog/logs_daemon/odmb75_${now}_daemon_output.txt

