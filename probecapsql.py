#!/usr/bin/python
# -*- coding: utf-8 -*-

import psycopg2
import sys
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

con = psycopg2.connect(database='postgres',
                 user='postgres',
                 host = 'localhost',
                 password='root')
print "Connecting to database\n    ->%s" % (con)

database = "wifi"
con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = con.cursor()

try:
    cur.execute("""select count(*) from information_schema.tables where table_name = 'station';""")
    if cur.fetchone()[0] == 1:
        print ("Database already exist")
        cur.close()
        con.close()
    
    else:
        cur.execute('CREATE DATABASE ' + database)
        cur.execute("""CREATE USER probecap WITH PASSWORD 'pass';""")
        cur.execute("""ALTER USER probecap WITH LOGIN;""")
        cur.execute("""ALTER USER probecap WITH SUPERUSER;""")
        cur.close()
        con.close()
        print ("Database created")
        
        con = psycopg2.connect(database='wifi',
                             user='probecap',
                             host = 'localhost',
                             password='pass')
        print "Connecting to database\n    ->%s" % (con)
        cur = con.cursor()
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur.execute('CREATE TABLE IF NOT EXISTS station(id serial not null UNIQUE,mac macaddr not null, model varchar(32), firstSeen timestamp without time zone not null,lastSeen timestamp without time zone,PRIMARY KEY(mac));')
        cur.execute('grant usage,select on sequence station_id_seq to probecap;')
        cur.execute('CREATE TABLE IF NOT EXISTS ssid(id serial not null UNIQUE,name varchar(32) not null, PRIMARY KEY(name));')
        cur.execute('grant usage,select on sequence ssid_id_seq to probecap;')
        cur.execute('CREATE TABLE IF NOT EXISTS probe(station int not null,foreign key (station) references station(id),ssid int null,foreign key (ssid) references ssid(id),seen timestamp without time zone);')
        cur.execute('CREATE TABLE IF NOT EXISTS beacon(station int not null,foreign key (station) references station(id),ssid int references ssid(id) null,seen timestamp without time zone);')
        cur.execute("""SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';""")
        result = cur.fetchall()
        print("Following tables have been created: " + str(result))
        cur.close()
        if con:
            con.close() 
        
except psycopg2.DatabaseError, e:
    print 'Error %s' % e    

 
#to delete the database and role run following 
#DROP DATABASE wifi 
#DROP OWNED BY probecap
#DROP ROLE probecap
