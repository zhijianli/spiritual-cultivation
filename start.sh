
mkdir -p /home/xiangli/spiritual-cultivation_log

# start chat server
pid=$(lsof -ti :5678) && if [ ! -z "$pid" ]; then kill $pid; fi
sleep 2
nohup python3 main.py  > /home/xiangli/spiritual-cultivation_log/log_dev.txt 2>&1 &

cd -
