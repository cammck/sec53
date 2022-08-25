#!/bin/sh
# launcher.sh - this is used by cron to restart the sec53 app after rebooting
# crontab usage : TBA
#
# navigate to home directory, then to this directory, then execute python script, then back home

cd /
cd home/sec53
sudo python sec53.py >/home/pi/sec53/logs/sec53.log 2>&1
cd /
