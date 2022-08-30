#!/usr/bin/python

import ConfigParser

config = ConfigParser.ConfigParser()
config.read('sec53.ini')

import time
import MySQLdb as mdb
import sys
import urllib
import urllib2
import datetime
from random import randint
#from pynma import PyNMA

def str_to_bool(s):
    if s == 'True':
         return True
    else:
         return False

debug = str_to_bool(config.get('GENERAL', 'debug'))

run_standalone = False
if (str_to_bool(config.get('GENERAL', 'run_standalone'))):
	print "Running in Stand-alone mode - NOT on Raspi!!!"
	run_standalone = True
	if debug:
		print "DEBUGGING is ON! "
	else:
		print "DEBUGGING is NOT on!"
else:
	import RPi.GPIO as GPIO

# Setup some global variables
version = "v{0} ".format(config.get('GENERAL', 'version'))
num_alerts = 0
MAX_ALERTS = 30

alert_time_reset = int(config.get('NOTIFICATIONS', 'SMS_alert_time_reset'))
SMSNotif_username = config.get('NOTIFICATIONS', 'username')
SMSNotif_password = config.get('NOTIFICATIONS', 'password')
SMSNotif_to = config.get('NOTIFICATIONS', 'to')

time_of_last_alert = None
check_GPIO = 0 # default to not checking - but check the database when starting up
alert_events = 0 # default to not alerting - but check the database when starting up
Running = True # set to running - used to restart
curr_control = "NOT SET"
consolidated_time_threshold = int(config.get('LOGGING', 'consolidated_time_threshold')) # number of seconds to consider an (active/open) event as part of previous event consolidation

# Define function for updating Database
def update_db(DB_connection, cursor, event_info, event = "GPIO Event detected"):
	"Updates DB connections and cursor with event text - update and commits the update"

	print "update_db - {0}: {1}".format(event, event_info)

	cursor.execute("INSERT INTO EvLog(EventDesc, EventInfo) VALUES('{0}', '{1}')".format(event, event_info))

	# after the PIR loop commit any DB changes to allow other apps (apache) to get updates
	DB_connection.commit()
	return;

# Define function for updating Database with GPIO events and consolidation of events if within a time threshold
def update_db_GPIO_event(DB_connection, cursor, GPIO_array, event_info, event = "GPIO Event detected"):
	"Consolidates GPIO events and updates DB connections and cursor with event text - update and commits the update,"

	GPIO_state = GPIO_array[4]							# current state of GPIO

	# If this is an "active" event (opened or activated) then write the event out to the consolidated table too
	# otherwise just send it to the full log (for closes and resets)
	if (GPIO_state):
		# Check the Event Tacker variable for this GPIO to determine whether this event is within the threshold to be consolidated (ie. within 15 seconds)

		current_time = time.time()							# Get the current time
		previous_GPIO_active_event_time = GPIO_array[8]		# previous GPIO active event time

		if debug:
			print "GPIO {0} - new state {1} - DB row Id {2} - prev time {3} - counter {4}".format(GPIO_array[0], GPIO_array[4], GPIO_array[7], GPIO_array[8], GPIO_array[9])
			if (previous_GPIO_active_event_time is not None):
				print "Previous active event time for {0} is {1} .. {2} ... ({3})".format(GPIO_array[0], previous_GPIO_active_event_time, current_time, current_time - previous_GPIO_active_event_time)
			else:
				print "No Previous active event time for {0}".format(GPIO_array[0])

		event_within_time_threshold = False

		# Get Previous active event time from the GPIO array for this event
		if (previous_GPIO_active_event_time is not None):
			time_diff = current_time - previous_GPIO_active_event_time
			if (time_diff <= consolidated_time_threshold):
				event_within_time_threshold = True

		if  (event_within_time_threshold):     # and (GPIO_array[7] != 0)):
			# Time now is within threshold time, so consolidate this event with previous entry
			# Get the current row id for this GPIO sensor to update
			GPIO_row_id = GPIO_array[7]

			# increment the counter only for active/open (1) states
			GPIO_counter = GPIO_array[9] + 1

			if debug:
				print "update_db_GPIO_event - UPDATE - {0}: {1} .. row id {2}".format(event, event_info, GPIO_row_id)

			# update the consolidated event log
			cursor.execute("UPDATE ConsolidatedEventLog SET EventDesc = '{0}', EventInfo = '{1} ({2})' where Id={3}".format('GPIO', event_info, GPIO_counter, GPIO_row_id))

			# increment counters
			GPIO_array[8] = current_time
			GPIO_array[9] = GPIO_counter
		else:
			# Time now is outside threshold time, so consider this a new event and reset counters

			# insert new consolidated event into the consolidated event log
			if debug:
				print "update_db_GPIO_event - INSERT - {0}: {1}".format(event, event_info)

			cursor.execute("INSERT INTO ConsolidatedEventLog(initial_ts, latest_ts, EventDesc, EventInfo) VALUES(null, null, '{0}', '{1}')".format('GPIO', event_info))

			row_id = cursor.lastrowid

			# reset counters
			GPIO_array[7] = row_id				# [7] - Previous record row ID to be used for updates to the database
			GPIO_array[8] = current_time		# [8] - Previous previous active time - to determine whether this event is new or should be consolidated
			GPIO_array[9] = 1					# [9] - Event count to be incremented for consolidated events, or reset for new events
	else:
		# if this is a de-activate event - we want to close the consolidated log off 
		print "Hi"

	# Pass the event onto the main log - Call the update_db function to write out the event details
	update_db(DB_connection, cursor, event_info)

	return;

# Define function for sending an alert
def send_alert(text_to_alert):
	"Sends an SMS alert - either via direct HTTPS call"
	global num_alerts
	global time_of_last_alert
	global alert_time_reset

	# check time_now is greater than time_of_last_alert + alert_time_reset
	current_time = time.time()

	print "Current time {0}".format(current_time)

	if (time_of_last_alert is not None):
		alert_time_diff = current_time - time_of_last_alert
	else:
		alert_time_diff = alert_time_reset + 1

	if ( alert_time_diff <= alert_time_reset ):
		print "Alert already sent within the last {0} seconds. Alerts will not be sent for the next {1} seconds!".format(alert_time_reset, alert_time_reset-alert_time_diff)
		update_db(con, cur, "{0} - Alert already sent within the last {1} seconds. Alerts will not be sent for the next {2} seconds!".format(text_to_alert, alert_time_reset, alert_time_reset-alert_time_diff), "ALERT NOT SENT!")
	else:
		time_of_last_alert = current_time

		#encode alert txt to replace spaces with %20 ... other characters? python function to encode?
		encoded_text_to_alert = urllib.quote(text_to_alert)
		sms_msg = "Security%20Event%20-%20{0}".format(encoded_text_to_alert)
		print "sms msg: {0}".format(sms_msg)

		sms_full_url = "https://api.smsbroadcast.com.au/api-adv.php?username={0}&password={1}&to={2}&from=Sec53&message={3}".format(SMSNotif_username, SMSNotif_password, SMSNotif_to, sms_msg)
		#sms_full_url = "https://api.smsbroadcast.com.au/api-adv.php?action=balance&username={0}&password={1}&to={2}&from=Sec53&message={3}".format(SMSNotif_username, SMSNotif_password, SMSNotif_to, sms_msg)

		# Need to check whether the alert is within the reset time
		if num_alerts < MAX_ALERTS:
			print "SEND ALERT!!! {0}".format(text_to_alert)

			response = urllib2.urlopen(sms_full_url)
			respcode =  response.info()

			# print out some server response info from SMS broadcast
			if debug:
				print respcode

			html = response.read()

			# do something
			response.close()  # best practice to close the file

			update_db(con, cur, "{0} - Alert count = {1} - resp = {2}".format(text_to_alert, num_alerts, html), "ALERT SENT!")
			num_alerts += 1
		else:
			print "ALERT NOT SENT - DUE TO MAX_ALERTS LIMIT{0}!!! {1}".format(num_alerts, text_to_alert)
			update_db(con, cur, "{0} - Alert count = {1}".format(text_to_alert, num_alerts), "ALERT NOT SENT!")

	return;

# Define function for updating Database
def check_Monitor_Control():
	global curr_control
	global check_GPIO
	global alert_events
	global Running

	# Check to see if monitoring has been switch off
	cur.execute("SELECT KeyPair FROM Control WHERE KeyVal = 'Monitor' limit 1")
	CONTROL_MONITOR = cur.fetchone()[0]

	# Check if the control monitor has changed from current
	if curr_control != CONTROL_MONITOR:
		curr_control = CONTROL_MONITOR

		if CONTROL_MONITOR == "ON":
			print "Switching GPIO checking on!"
			update_db(con, cur, version + "Switching GPIO checking ON!", "CONTROL_MONITOR has changed in the main loop")

			# Send NMA push notification
			#res = p.push("Sec53", 'GPIO switch', 'Switching GPIO checking on!', 'http://mckerral.ddns.net/sec53/events.php', batch_mode=False)
			check_GPIO = 1
			alert_events = 0
		elif CONTROL_MONITOR == "ALERT":
			print "Switching GPIO checking on with Alerting!"
			update_db(con, cur, version + "Switching GPIO checking ON with ALERTING!", "CONTROL_MONITOR has changed in the main loop")

			check_GPIO = 1
			alert_events = 1
		elif CONTROL_MONITOR == "RESTART":
			print "Quitting! So that Sec53 can be restarted!"
			update_db(con, cur, version + "Restart required!", "CONTROL_MONITOR has changed in the main loop")

			# Check to see what the previous monitoring was so that we can revert after restart
			cur.execute("SELECT KeyPair FROM Control WHERE KeyVal = 'MonitorPreviousState' limit 1")
			row = cur.fetchone()
			if row:
				PREV_STATE = row[0]
			else:
				# Could not retrieve previous State so set to default - ALERT
				PREV_STATE = "ALERT"
				cursor.execute("INSERT INTO Control(KeyVal, KeyPair) VALUES('MonitorPreviousState', '')".format(PREV_STATE))

			# Reset on ON so that it will be running after restart
			cur.execute("UPDATE Control SET KeyPair = %s WHERE KeyVal = %s", (PREV_STATE, "Monitor"))

			# Set some values to drop out of the main loop
			Running = False
			check_GPIO = 0
			alert_events = 0
			con.commit()
			con.close()
		elif CONTROL_MONITOR == "OFF":
			print "Switching GPIO checking OFF!"
			update_db(con, cur, version + "Switching GPIO checking OFF!", "CONTROL_MONITOR has changed in the main loop")
			check_GPIO = 0
			alert_events = 0
		else:
			# Default to checking but not alerting if a known value is not found
			update_db(con, cur, version + "Switching GPIO checking ON!", "CONTROL_MONITOR has changed in the main loop to invalid value {$0}".format(CONTROL_MONITOR))
			check_GPIO = 1
			alert_events = 0

	return;

# Setup initial values
if (not run_standalone):
	GPIO.setmode(GPIO.BCM)

GPIO_FRONT_DOOR = 18
GPIO_GARAGE_DOOR = 17
GPIO_LAUNDY_DOOR = 22
GPIO_BACK_SLIDING_DOORS = 00
GPIO_HALL_PIR = 23
GPIO_UPSTAIRS_PIR = 00
GPIO_STUDY_PIR = 27

# PIR_ARRAY details
# [0] - PIR description
# [1] - PIR GPIO identifier (see above)
# [2] - PIR enabled/disabled switch - 1 = enabled, 0 = disabled
# [3] - REED (door) switch or PIR (Passive Infra Red) motion sensor
# [4] - state register for the PIR - used to hold state and understand state changes
# [5] - text to display when PIR is in open/active state usually "opened" for REED switches and "detected" for PIR sensors
# [6] - text to display when PIR is in closed/deactive state usually "closed" for REED switches and "reset" for PIR sensors
# [7] - NEW for consolidation - Previous record row ID to be used for updates to the database
# [8] - NEW for consolidation - Previous previous active time - to determine whether this event is new or should be consolidated
# [9] - NEW for consolidation - Event count to be incremented for consolidated events, or reset for new events
PIR_ARRAY = [[0 for x in range(10)] for x in range(8)]

PIR_ARRAY[0][0] = "Front Door"
PIR_ARRAY[0][1] = GPIO_FRONT_DOOR
PIR_ARRAY[0][2] = 1
PIR_ARRAY[0][3] = "REED"
PIR_ARRAY[0][5] = "Opened"
PIR_ARRAY[0][6] = "Closed"
PIR_ARRAY[0][7] = 0
PIR_ARRAY[0][8] = None
PIR_ARRAY[0][9] = 1

PIR_ARRAY[1][0] = "Garage Door"
PIR_ARRAY[1][1] = GPIO_GARAGE_DOOR
PIR_ARRAY[1][2] = 1
PIR_ARRAY[1][3] = "REED"
PIR_ARRAY[1][5] = "Opened"
PIR_ARRAY[1][6] = "Closed"
PIR_ARRAY[1][7] = 0
PIR_ARRAY[1][8] = None
PIR_ARRAY[1][9] = 1

PIR_ARRAY[2][0] = "Laundry Door"
PIR_ARRAY[2][1] = GPIO_LAUNDY_DOOR
PIR_ARRAY[2][2] = 1
PIR_ARRAY[2][3] = "REED"
PIR_ARRAY[2][5] = "Opened"
PIR_ARRAY[2][6] = "Closed"
PIR_ARRAY[2][7] = 0
PIR_ARRAY[2][8] = None
PIR_ARRAY[2][9] = 1

PIR_ARRAY[3][0] = "Back Sliding Door"
PIR_ARRAY[3][1] = GPIO_BACK_SLIDING_DOORS
PIR_ARRAY[3][2] = 0
PIR_ARRAY[3][3] = "REED"
PIR_ARRAY[3][5] = "Opened"
PIR_ARRAY[3][6] = "Closed"
PIR_ARRAY[3][7] = 0
PIR_ARRAY[3][8] = None
PIR_ARRAY[3][9] = 1

PIR_ARRAY[4][0] = "Hall motion"
PIR_ARRAY[4][1] = GPIO_HALL_PIR
PIR_ARRAY[4][2] = 1
PIR_ARRAY[4][3] = "PIR"
PIR_ARRAY[4][5] = "Detected"
PIR_ARRAY[4][6] = "Reset"
PIR_ARRAY[4][7] = 0
PIR_ARRAY[4][8] = None
PIR_ARRAY[4][9] = 1

PIR_ARRAY[5][0] = "Upstairs motion"
PIR_ARRAY[5][1] = GPIO_UPSTAIRS_PIR
PIR_ARRAY[5][2] = 0
PIR_ARRAY[5][3] = "PIR"
PIR_ARRAY[5][5] = "Detected"
PIR_ARRAY[5][6] = "Reset"
PIR_ARRAY[5][7] = 0
PIR_ARRAY[5][8] = None
PIR_ARRAY[5][9] = 1

PIR_ARRAY[6][0] = "Study motion"
PIR_ARRAY[6][1] = GPIO_STUDY_PIR
PIR_ARRAY[6][2] = 1
PIR_ARRAY[6][3] = "PIR"
PIR_ARRAY[6][5] = "Detected"
PIR_ARRAY[6][6] = "Reset"
PIR_ARRAY[6][7] = 0
PIR_ARRAY[6][8] = None
PIR_ARRAY[6][9] = 1

print "Starting Sec53 {0}".format(version)

# Connect to Database to determine monitor status
DB_not_ready = 1
while DB_not_ready:
	try:
		con = mdb.connect('localhost', 'secuser', 'secuser53', 'sec53');
		cur = con.cursor()
		cur.execute("SELECT VERSION()")
		ver = cur.fetchone()
		print "MySql DB version : %s " % ver

		cur.execute("set session transaction isolation level READ COMMITTED")
		DB_not_ready = 0

	except mdb.Error, e:
		print "Error %d: %s" % (e.args[0],e.args[1])
		time.sleep(2)
		#sys.exit(1)

# setup inital values of the PIRs
for PIR in PIR_ARRAY:
	# if this PIR is active [2] = 1 then probe it.
	if PIR[2]:
		if (not run_standalone):
			GPIO.setup(PIR[1], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
			GPIO_value  = GPIO.input(PIR[1])
		else:
			# Setup temporary GPIO_value of 0
			GPIO_value = 0

		if GPIO_value == 1:
			evtext = "{0} {1} - GPIO {2}".format(PIR[0], PIR[5], GPIO_value)
			update_db(con, cur, evtext, "WARNING DURING START-UP")

		if debug:
			print "Setting initial value for {0} - {1}".format(PIR[0], GPIO_value)
		PIR[4] = GPIO_value

print "Waiting for PIR to settle ..."

if (not run_standalone):
	# Loop until PIR output is 0 (no motion)
	while GPIO.input(GPIO_STUDY_PIR)==1:
		Current_State  = 0

print "  Ready"

update_db(con, cur, version, "Starting up Sec53")

Running = True

try:
	while Running:
		check_Monitor_Control()
		alert_this_event = False

		while check_GPIO:
			# Loop over the PIR array
			for PIR in PIR_ARRAY:
				# if this PIR is active (because [2] = 1) then probe it.
				if PIR[2]:
					if (not run_standalone):
						# Get the current state of each sensor
						current_state = GPIO.input(PIR[1])
					else:
						# Get a random number to simulate a GPIO event
						event = randint(0, 500)
						if (event <= 1):
							# If a desired random number was hit - then switch the state On(1) if Off(0) and Off(0) if On(1)
							current_state = (PIR[4] + 1) % 2
							if debug:
								print "Switch {0} was {1} now {2}".format(PIR[0], PIR[4], current_state)
						else:
							# Otherwise keep the current state
							current_state = PIR[4]
							# Maybe try to force reset a sensor after 3 seconds to simulate a PIR reset??? PIR only???

					# if the probe value is different to the previous value
					if current_state != PIR[4]:
						reset_event = False;
						# if the new state is high (open or motion) report it to DB
						if current_state == 1:
							ev_text = "{0} {1}".format(PIR[0], PIR[5])
							
							if alert_events:
							    alert_this_event = True
						else:
							ev_text = "{0} {1}".format(PIR[0], PIR[6])
							if PIR[6] == "Reset":
								reset_event = True;

						# Record the current state for future reference
						PIR[4] = current_state

						# write the event text to the database
						if not reset_event:
							update_db_GPIO_event(con, cur, PIR, ev_text);

						if alert_this_event:
							send_alert(ev_text)

							# Reset the alert flag
							alert_this_event = False

			# Have a same sleep before looping and checking again
			time.sleep(0.1)

			# Check to see if monitoring has been switch off
			check_Monitor_Control()

		# Sleep for a little before checking the DB again
		time.sleep(2)


except KeyboardInterrupt:
	print "  Quit"

	if (not run_standalone):
		GPIO.cleanup() # Reset GPIO settings

	if con:
		update_db(con, cur, "Keyboard Interrupt", "Quitting!")

		con.close()

