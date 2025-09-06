# HTTP SERVICE

## RUN ON VPS
python3 app.py

## TEST:

=======================vvvvvvvvvvvvv================= Replace with your own VPS IP
curl -s -X POST http://159.65.125.83:8081/partition \
  -H 'Content-Type: application/json' \
  -d '{"subnet":"10.189.24.0/24","dim":[10,10,100]}' | jq
