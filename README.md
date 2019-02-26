# sec53
Raspberry PI based security system for Door (reed) sensors and motion (PIR) sensors

This is a long running project that doesn't get a lot of attention but still ticks away at the bottom of my todo list. Here is what is currently does and some of the things that I have planned for it in future (when time permits, and/or when an important use case comes up)!

## What it does
* Allows for mutiple REED (door) sensors and PIR (motion) sensors to record events into local MySql DB
* Web interface to view events (sensor trigger & reset) by day
* Web interface to change mode from 
  * OFF - don't record anything
  * MONITOR - record all sensor trigger and reset events, but don't actively do anything with the events
  * ALERT - as for MONITOR but also send SMS message to 1 or more mobile numbers (within certain limits/caps) - requires SMS servive subscription (SMS Broadcast is used currently as it's local (MELB/AUST) and reasonably priced)
  * RESTART - restart the python app
* Use Google MFA (Multi-Function Authentication) to ensure that only authorised users can change the mode - Hoping that this can be removed if I figure out the best (and most secure) way to integrate mutual auth certs to ensure that only users with the appropriate certificate can view and interact with Sec53 - (see _https://www.instructables.com/id/Restrict-Access-to-Raspberry-Pi-Web-Server/_)

_other notes_
* ALERT mode can be configured to set limits to number of text messages per day (default is max 30) - resets at midnight.
* ALERT mode can be configured to not re-alert within a specific timeframe (default 30s - I think)
* ALERT mode can be configured to send message to multiple mobile numbers

## Plans for the Future / TODO
* Add doc and or diagrams to GitHub to show the wiring setup (based on http://projects.privateeyepi.com/home/home-alarm-system-project/installation/alarm-electronics)
* Add docs an/or scripts used to setup Raspi
* Add ability to use push notifications instead of SMS
* Add temp sensors (1/2 done already - but only works with 1 temp sensor and doesn't show data/events)
* jazz up the web interface to make more family friendly (maybe iOS APP - sorry only apple users in my home!)
* get better insights from the event data (ties into AWS ML below)
* add mutual authentication support - to allow for family members to use without MFA codes
* add ability to open/close garage door for remote visitor access
* integrate with AWS to off load the heavy data from events
* integrate with AWS machine learning to try to figure out normal events versus an actual security event
* graphing events for better visualisation???
* ...

## files:
* LICENSE	- standard license file
* README.md	- this file
* launcher.sh	 - bash script for launching Sec53 using cron - need to add cron usage as comment
* pirloop.py	- simple sensor setup and loop script to test sensor connections, etc
* pirloop 2.py	- not sure how this is different to the file above - probably should consolidate and remove this one
* sec53-db-setup.py	- script to setup MySql CONTROL table - needs update to use INI file instead of hardcoded values
* sec53-db-log-setup.py - script to setup MySql EVENTS table - needs update to use INI file instead of hardcoded values
* sec53-monitor-off.py	- script to turn monitoring OFF from the command line  - needs update to use INI file instead of hardcoded values
* sec53-monitor-on.py	- script to turn monitoring ON from the command line  - needs update to use INI file instead of hardcoded values
* sec53.ini	- initialisation file used to store key parameters - such as DB config and notification details
* sec53.py	 - main python script to handle event logging and notifications

_What about the missing files? ALERT script. Seems files need updating with current version! *TODO FEB 2019* 

