#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb as mdb
from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
parser.read('sec53.ini')

server = parser.get('Database', 'server_name')
db = parser.get('Database', 'database')
username = parser.get('Database', 'user_name')
password = parser.get('Database', 'password')
con = mdb.connect(server, username, password, db);
# con = mdb.connect('localhost', 'secuser', 'secuser53', 'sec53');

with con:    
	cur = con.cursor()

	cur.execute("SELECT KeyPair FROM Control WHERE KeyVal = 'Monitor' limit 1")
	print "Monitor previously set to ", cur.fetchone()[0]

	cur.execute("UPDATE Control SET KeyPair = %s WHERE KeyVal = %s", ("ON", "Monitor"))   	

	cur.execute("SELECT KeyPair FROM Control WHERE KeyVal = 'Monitor' limit 1")
	print "Monitor now set to ", cur.fetchone()[0]

	con.commit()
