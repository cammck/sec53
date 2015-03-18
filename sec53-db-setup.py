#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb as mdb

con = mdb.connect('localhost', 'secuser', 'secuser53', 'sec53');

with con:    
	cur = con.cursor()
	cur.execute("DROP TABLE IF EXISTS Control")
	cur.execute("CREATE TABLE Control(Id INT PRIMARY KEY AUTO_INCREMENT, KeyVal VARCHAR(25), KeyPair VARCHAR(25))")
	cur.execute("INSERT INTO Control(KeyVal, KeyPair) VALUES('Monitor', 'OFF')")

