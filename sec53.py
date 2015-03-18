#!/usr/bin/python

import RPi.GPIO as GPIO 
import time
import MySQLdb as mdb
import sys
from pynma import PyNMA

# Setup initial values
GPIO.setmode(GPIO.BCM)

GPIO_FRONT_DOOR = 18
GPIO_GARAGE_DOOR = 17
GPIO_LAUNDY_DOOR = 22
GPIO_BACK_SLIDING_DOORS = 00
GPIO_HALL_PIR = 00
GPIO_UPSTAIRS_PIR = 00
GPIO_STUDY_PIR = 27

# setup PIR array
PIR_ARRAY = [[0 for x in range(5)] for x in range(8)]
#PIR_ARRAY = [[]]
PIR_ARRAY[0][0] = "Front Door"
PIR_ARRAY[0][1] = GPIO_FRONT_DOOR
PIR_ARRAY[0][2] = 1
PIR_ARRAY[0][3] = "REED"
PIR_ARRAY[1][0] = "Garage Door"
PIR_ARRAY[1][1] = GPIO_GARAGE_DOOR
PIR_ARRAY[1][2] = 1
PIR_ARRAY[1][3] = "REED"
PIR_ARRAY[2][0] = "Laundry Door"
PIR_ARRAY[2][1] = GPIO_LAUNDY_DOOR
PIR_ARRAY[2][2] = 1
PIR_ARRAY[2][3] = "REED"
PIR_ARRAY[3][0] = "Back Sliding Door"
PIR_ARRAY[3][1] = GPIO_BACK_SLIDING_DOORS
PIR_ARRAY[3][2] = 0
PIR_ARRAY[3][3] = "REED"
PIR_ARRAY[4][0] = "Hall motion"
PIR_ARRAY[4][1] = GPIO_HALL_PIR
PIR_ARRAY[4][2] = 0
PIR_ARRAY[4][3] = "PIR"
PIR_ARRAY[5][0] = "Upstairs motion"
PIR_ARRAY[5][1] = GPIO_UPSTAIRS_PIR
PIR_ARRAY[5][2] = 0
PIR_ARRAY[5][3] = "PIR"
PIR_ARRAY[6][0] = "Study motion"
PIR_ARRAY[6][1] = GPIO_STUDY_PIR
PIR_ARRAY[6][2] = 1
PIR_ARRAY[6][3] = "PIR"

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
		GPIO.setup(PIR[1], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		GPIO_value  = GPIO.input(PIR[1])
		if GPIO_value == 1:
			if PIR[3] == "REED":
				cur.execute("INSERT INTO EventLog(EventDesc, EventInfo) VALUES('WARNING: Door Open during Start-up', '{0} - GPIO {1}')".format(PIR[0], GPIO_value))
			if PIR[3] == "PIR":
				cur.execute("INSERT INTO EventLog(EventDesc, EventInfo) VALUES('WARNING: Motion detected during Start-up', '{0} - GPIO {1}')".format(PIR[0], GPIO_value))
			con.commit()
		print "Setting initial value for {0} - {1}".format(PIR[0], GPIO_value)
		PIR[4] = GPIO_value

#GPIO.setup(GPIO_HALL_PIR, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

print "Waiting for PIR to settle ..."

# Loop until PIR output is 0 (no motion)
while GPIO.input(GPIO_STUDY_PIR)==1:
	Current_State  = 0
print "  Ready"

p = PyNMA()
p.addkey("769dd5e70415a3e4610298ac28176229c2fa33f068eedbb7")




try:
	while True:
		cur.execute("SELECT KeyPair FROM Control WHERE KeyVal = 'Monitor' limit 1")
		CONTROL_MONITOR = cur.fetchone()[0]
		if CONTROL_MONITOR == "ON":
			print "Switching GPIO checking on!"
			cur.execute("INSERT INTO EventLog(EventDesc, EventInfo) VALUES('Switching GPIO checking ON!', 'CONTROL_MONITOR has changed in main loop.')")
			con.commit()
			# Send NMA push notification
			res = p.push("Sec53", 'GPIO switch', 'Switching GPOI checking on!', 'http://mckerral.ddns.net/Sec53/events.php', batch_mode=False)
			check_GPIO = 1
		else:
			check_GPIO = 0

		while check_GPIO:
			for PIR in PIR_ARRAY:
				# if this PIR is active [2] = 1 then probe it.
				if PIR[2]:

					current_state = GPIO.input(PIR[1])

					# if the probe value is different to the previous value$
					if current_state != PIR[4]:
						# if the new state is high (open or motion)
						if current_state == 1:
							if PIR[3] == "REED":
								print "{0} - Opened".format(PIR[0])
								cur.execute("INSERT INTO EventLog(EventDesc, EventInfo) VALUES('GPIO Event detected', '{0} Opened')".format(PIR[0]))
							if PIR[3] == "PIR":
								print "{0} detected".format(PIR[0])
								cur.execute("INSERT INTO EventLog(EventDesc, EventInfo) VALUES('GPIO Event detected', '{0} detected')".format(PIR[0]))
						else:
							if PIR[3] == "REED":
								print "{0} - Closed".format(PIR[0])
								cur.execute("INSERT INTO EventLog(EventDesc, EventInfo) VALUES('GPIO Event detected', '{0} Closed')".format(PIR[0]))
							if PIR[3] == "PIR":
								print "{0} reset".format(PIR[0])
								cur.execute("INSERT INTO EventLog(EventDesc, EventInfo) VALUES('GPIO Event detected', '{0} reset')".format(PIR[0]))
						PIR[4] = current_state

			# after the PIR loop commit any DB changes to allow other apps (apache) to get updates
			con.commit()

			time.sleep(0.1)

			cur.execute("SELECT KeyPair FROM Control WHERE KeyVal = 'Monitor' limit 1")
			CONTROL_MONITOR = cur.fetchone()[0]

			if CONTROL_MONITOR == "OFF":
				print "Switching GPIO checking OFF!"
				cur.execute("INSERT INTO EventLog(EventDesc, EventInfo) VALUES('Switching GPIO checking OFF!', 'CONTROL_MONITOR has changed in GPIO loop.')")
				con.commit()
				# Send NMA push notification
				res = p.push("Sec53", 'GPIO switch', 'Switching GPOI checking OFF!', 'http://mckerral.ddns.net/Sec53/events.php', batch_mode=False)
				check_GPIO = 0

		# Sleep for a little before checking the DB again
		time.sleep(2)


except KeyboardInterrupt:
	print "  Quit"
	# Reset GPIO settings
	GPIO.cleanup()
	if con:
		cur.execute("INSERT INTO EventLog(EventDesc, EventInfo) VALUES('Quitting!', 'Keyboard Interrupt')")
		con.commit()
		con.close()

