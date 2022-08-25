#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb as mdb
import time

con = mdb.connect('localhost', 'secuser', 'secuser53', 'sec53');

with con:    
	cur = con.cursor()
	cur.execute("DROP TABLE IF EXISTS EventLog")
	cur.execute("CREATE TABLE EventLog(Id INT PRIMARY KEY AUTO_INCREMENT, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP, EventDesc VARCHAR(250), EventInfo VARCHAR(250))")

	cur.execute("INSERT INTO EventLog(EventDesc, EventInfo) VALUES('Created Event Log Table', 'Initial creation of Event Log Table')")
	
	cur.execute("DROP TABLE IF EXISTS ConsolidatedEventLog")
	cur.execute("CREATE TABLE ConsolidatedEventLog(Id INT PRIMARY KEY AUTO_INCREMENT, initial_ts TIMESTAMP DEFAULT '0000-00-00 00:00:00', latest_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP, duration INT, EventDesc VARCHAR(250), EventInfo VARCHAR(250))")
	
	# Create INSERT and UPDATE triggers to calculate the duration column based on the difference between initial_ts and latest_ts
	#cur.execute("DROP TRIGGER IF EXISTS InsertEventDuration")
	#cur.execute("DROP TRIGGER IF EXISTS UpdateEventDuration")
	cur.execute("CREATE TRIGGER InsertEventDuration BEFORE INSERT ON ConsolidatedEventLog FOR EACH ROW BEGIN SET NEW.duration = TIMESTAMPDIFF(SECOND, NEW.initial_ts, NEW.latest_ts); END")	
	cur.execute("CREATE TRIGGER UpdateEventDuration BEFORE UPDATE ON ConsolidatedEventLog FOR EACH ROW BEGIN SET NEW.latest_ts=CURRENT_TIMESTAMP; SET NEW.duration = TIMESTAMPDIFF(SECOND, NEW.initial_ts, NEW.latest_ts); END")

	cur.execute("INSERT INTO ConsolidatedEventLog(initial_ts, EventDesc, EventInfo) VALUES(null, 'Created Consolidated Event Log Table', 'Initial creation of Consolidated Event Log Table')")

	time.sleep(1)

	cur.execute("UPDATE ConsolidatedEventLog SET EventDesc = 'Updated Consolidated Event Log Table' where Id=1")
	
# NOTE:
# ConsolidatedEventLog uses a trick of:
#		initial_ts TIMESTAMP DEFAULT '0000-00-00 00:00:00'
# due to mysql 5.5 (on the Raspi) not allowing multiple TIMESTAMP columns with CURRENT_TIMESTAMP in DEFAULT or ON UPDATE see below error
# 		Error: 1293, 'Incorrect table definition; there can be only one TIMESTAMP column with CURRENT_TIMESTAMP in DEFAULT or ON UPDATE clause'
# This trick means that for any insert initial_ts needs to be set to 'null' on insert ... but it seems to work. More details:
# http://stackoverflow.com/questions/267658/having-both-a-created-and-last-updated-timestamp-columns-in-mysql-4-0/267675#267675 or
# http://gusiev.com/2009/04/update-and-create-timestamps-with-mysql/


