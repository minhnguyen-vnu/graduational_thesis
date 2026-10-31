#!/bin/bash
cd "$(dirname "$0")" || exit 2
until python3 driver.py; do
  echo "$(date '+%F %T') driver thoat bat thuong, khoi dong lai sau 60 giay" >> run.log
  sleep 60
done
python3 select_queue.py >> run.log 2>&1
echo "$(date '+%F %T') PIPELINE DONE rc=$?" >> run.log
touch PIPELINE-DONE
