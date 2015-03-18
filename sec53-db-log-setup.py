#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb as mdb

con = mdb.connect('localhost', 'secuser', 'secuser53', 'sec53');

with con:    
	cur = con.cursor()
	cur.execute("DROP TABLE IF EXISTS EventLog")
	cur.execute("CREATE TABLE EventLog(Id INT PRIMARY KEY AUTO_INCREMENT, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP, EventDesc VARCHAR(250), EventInfo VARCHAR(250))")

	cur.execute("INSERT INTO EventLog(EventDesc, EventInfo) VALUES('Created Event Log Table', 'Initial creation of Event Log Table')")

