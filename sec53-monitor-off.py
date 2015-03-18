#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb as mdb

con = mdb.connect('localhost', 'secuser', 'secuser53', 'sec53');

with con:    
	cur = con.cursor()

	cur.execute("SELECT KeyPair FROM Control WHERE KeyVal = 'Monitor' limit 1")
	print "Monitor previously set to ", cur.fetchone()[0]

	cur.execute("UPDATE Control SET KeyPair = %s WHERE KeyVal = %s", ("OFF", "Monitor"))   	

	cur.execute("SELECT KeyPair FROM Control WHERE KeyVal = 'Monitor' limit 1")
	print "Monitor now set to ", cur.fetchone()[0]

	con.commit()
