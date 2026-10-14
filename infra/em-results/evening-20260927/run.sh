#!/usr/bin/env zsh
set -u
R=/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/em-results
echo "$(date +%H:%M:%S) bat dau Airflow hai nhanh cache_ttl" > $R/evening-20260927/progress.log
zsh $R/airflow-ttl-20260927/run.sh > $R/airflow-ttl-20260927/run-nohup.out 2>&1
echo "$(date +%H:%M:%S) Airflow exit $?; bat dau Vikunja spec co example" >> $R/evening-20260927/progress.log
zsh $R/vikunja-examples-20260927/run.sh > $R/vikunja-examples-20260927/run-nohup.out 2>&1
echo "$(date +%H:%M:%S) Vikunja exit $?" >> $R/evening-20260927/progress.log
echo "$(date +%H:%M:%S) bat dau pyLoad ban da va seeds 1-20" >> $R/evening-20260927/progress.log
zsh $R/pyload-fixed-tt-20260927/run.sh > $R/pyload-fixed-tt-20260927/run-nohup.out 2>&1
echo "$(date +%H:%M:%S) pyLoad ban da va exit $?" >> $R/evening-20260927/progress.log
echo "$(date +%H:%M:%S) bat dau pyLoad ban loi seeds 12-20" >> $R/evening-20260927/progress.log
zsh $R/pyload-vuln-tt-12-20-20260927/run.sh > $R/pyload-vuln-tt-12-20-20260927/run-nohup.out 2>&1
echo "$(date +%H:%M:%S) pyLoad ban loi 12-20 exit $?" >> $R/evening-20260927/progress.log
echo "EVENING DONE $(date)" >> $R/evening-20260927/progress.log
