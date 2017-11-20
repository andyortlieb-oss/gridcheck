#!/usr/bin/env sh

GRIDCHECK_SEED_HOST=http://google.com:80 GRIDCHECK_ROUTABLE_IP=127.0.0.1 GRIDCHECK_ROUTABLE_PORT=1001 python gridcheck/supervisor.py --seed-host http://127.0.0.1:8001 --seed-host http://127.0.0.1:8002 --seed-host http://127.0.0.1:8003 --routable-hostname=localhost --check-config
