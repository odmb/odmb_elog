#!/bin/bash
daemon(){
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

now=$(date "+%m_%d_%y__%H_%M_%S")
"$@" > /data/odmb75_database/odmb_elog/logs_daemon/odmb75_${now}_daemon_output.txt
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
