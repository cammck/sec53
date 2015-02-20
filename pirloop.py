#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import MySQLdb as mdb
import sys
import random


# setup PIR array
PIR_ARRAY = [[0 for x in range(5)] for x in range(8)]
#PIR_ARRAY = [[]]
PIR_ARRAY[0][0] = "Front Door"
PIR_ARRAY[0][1] = 17
PIR_ARRAY[0][2] = 1
PIR_ARRAY[0][3] = "REED"
PIR_ARRAY[1][0] = "Garage Door"
PIR_ARRAY[1][1] = 0
PIR_ARRAY[1][2] = 0
PIR_ARRAY[1][3] = "REED"
PIR_ARRAY[2][0] = "Laundry Door"
PIR_ARRAY[2][1] = 0
PIR_ARRAY[2][2] = 0
PIR_ARRAY[2][3] = "REED"
PIR_ARRAY[3][0] = "Back Sliding Door"
PIR_ARRAY[3][1] = 0
PIR_ARRAY[3][2] = 0
PIR_ARRAY[3][3] = "REED"
PIR_ARRAY[4][0] = "Hall motion"
PIR_ARRAY[4][1] = 27
PIR_ARRAY[4][2] = 1
PIR_ARRAY[4][3] = "PIR"
PIR_ARRAY[5][0] = "Upstairs motion"
PIR_ARRAY[5][1] = 0
PIR_ARRAY[5][2] = 0
PIR_ARRAY[5][3] = "PIR"
PIR_ARRAY[6][0] = "Study motion"
PIR_ARRAY[6][1] = 0
PIR_ARRAY[6][2] = 0
PIR_ARRAY[6][3] = "PIR"

# setup inital values of the PIRs
PIR_ARRAY[0][4] = 0
PIR_ARRAY[1][4] = 0
PIR_ARRAY[2][4] = 0
PIR_ARRAY[3][4] = 0
PIR_ARRAY[4][4] = 0
PIR_ARRAY[5][4] = 0
PIR_ARRAY[6][4] = 0

while True:
	for PIR in PIR_ARRAY:
		# if this PIR is active [2] = 1 then probe it.
		if PIR[2]:
	
			current_state = random.randint(0,1) #GPIO.input(PIR[1])
			print "random - {0}".format(current_state)
			# if the probe value is different to the previous value [4] log it
			if current_state != PIR[4]:
				if current_state == 1:
					if PIR[3] == "REED":
						print "{0} - Opened".format(PIR[0])
						#cur.execute("INSERT INTO EventLog(Event$
					if PIR[3] == "PIR":
						print "{0} detected".format(PIR[0])
						#cur.execute("INSERT INTO EventLog(Event$
				else:
					if PIR[3] == "REED":
						print "{0} - Closed".format(PIR[0])
						#cur.execute("INSERT INTO EventLog(Event$
					if PIR[3] == "PIR":
						print "{0} reset".format(PIR[0])
						#cur.execute("INSERT INTO EventLog(Event$
#                               	 con.commit()
				PIR[4] = current_state
