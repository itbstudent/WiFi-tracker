import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

from scapy.all import sniff
from scapy.layers.dot11 import Dot11
import sys
import struct
import psycopg2
import manuf 
import os
import time

MGMT_TYPE = 0x0
PROBE_SUBTYPE = 0x04
BEACON_SUBTYPE = 0x08

FMT_HEADER_80211 = "<HH6s6s6sH"
WLAN_MGMT_ELEMENT = "<BB"
BEACON_FIXED_PARAMETERS = "<xxxxxxxxHH"

TO_DS_BIT = 2**9
FROM_DS_BIT = 2**10

def encodeMac(s):
    return ''.join(( '%.2x' % ord(i) for i in s ))

class Handler(object):
    def __init__(self):
        self.conn = None
        
    def getDatabaseConnection(self):
    
        if self.conn == None:
            self.conn = psycopg2.connect(database='wifi', user='probecap', host = 'localhost', password='pass')
            
        return self.conn
    
    def channel_hopping(self):
        chans = range(14)
        wait = 1
        i = 0
        while True:
            os.system('iw dev wlan0 set channel %d' % chans[i])
            i = (i + 1) % len(chans)
            time.sleep(wait)
            print i

        
    def __call__(self,pkt):
        #If the packet is not a management packet ignore it
        
        if not pkt.haslayer(Dot11):
            return
            
        if not pkt.type == MGMT_TYPE:
            return
        
        isBeacon = pkt.subtype == BEACON_SUBTYPE
        isProbe = pkt.subtype == PROBE_SUBTYPE
        if not (isBeacon or isProbe):
            return
        
                        #Extract the payload from the packet
        payload = buffer(str(pkt.payload))
        #Carve out just the header
        headerSize = struct.calcsize(FMT_HEADER_80211)
        header = payload[:headerSize]
        #unpack the header
        frameControl,dur,addr1,addr2,addr3,seq = struct.unpack(FMT_HEADER_80211,header)
        
        fromDs = (FROM_DS_BIT & frameControl) != 0
        toDs = (TO_DS_BIT & frameControl) != 0
        
        if fromDs and not toDs:
            srcAddr = addr3
        elif not  fromDs and not toDs:
            srcAddr = addr2
        elif not fromDs and toDs:
            srcAddr = addr2
        elif fromDs and toDs:
            return
        
        #Query the database to see the last time this station was seen
        conn = self.getDatabaseConnection()
        cur = conn.cursor()
        
        cur.execute("Select id,lastseen from station where mac = %s;",(encodeMac(srcAddr),))
        r = cur.fetchone()
        mac = encodeMac(srcAddr)
        #If never seen, add the station to the database
        if r == None:
            ##############GETTING MODEL BY MAC###################
            getmac = manuf.MacParser()
            model = getmac.get_manuf(mac)
            print model,mac
            #####################################################
            
            ###############TELEGRAM BOT########################### 
            #sending alert when new Mac is found
            #bot = telegram.Bot(token='203410933:AAG6avZhedGbVsGZjgEa1x5u-DuNZ3BcjTE')
            #updates = bot.getUpdates()
            #chat_id = '199913115'
            #bot.sendMessage(chat_id=chat_id, text='ALERT! Wifi perimeter violation Mac %s Model %s' % (mac,model,))
            ######################################################
            
            #insert new mac into DB
            cur.execute("""Insert into station(mac, model, firstSeen,lastSeen) VALUES(%s, %s, current_timestamp at time zone 'utc',current_timestamp at time zone 'utc') returning id;""",(encodeMac(srcAddr),model,))
            r = cur.fetchone()
            suid = r
        #If seen, update the last seen time of the station 
        else:
            suid,lastSeen = r
            cur.execute("Update station set lastSeen = current_timestamp at time zone 'utc' where id = %s",(suid,))
        cur.close()
        conn.commit()

        #Extract each tag from the payload
        tags = payload[headerSize:]
        
        if isBeacon:
            tags = tags[struct.calcsize(BEACON_FIXED_PARAMETERS):]
        
        ssid = None
        while len(tags) != 0:
            #Carve out and extract the id and length of the  tag
            tagHeader = tags[0:struct.calcsize(WLAN_MGMT_ELEMENT)]
            tagId,tagLength = struct.unpack(WLAN_MGMT_ELEMENT,tagHeader)
            tags = tags[struct.calcsize(WLAN_MGMT_ELEMENT):]

            #The tag id must be zero for SSID
            #The tag length must be greater than zero or it is a 
            #an anonymous probe
            #The tag length must be less than or equal to 32 or it is
            #not a valid SSID

            if tagId == 0 and tagLength !=0 and tagLength <=32:
                ssid = tags[:tagLength]
                
                #Made sure what is extracted is valid ASCII
                #Psycopg2 pukes otherwise
                try:
                    ssid = ssid.decode('ascii')
                except UnicodeDecodeError:
                    ssid = None
                    continue
                
                break 
                
            tags = tags[tagLength:]
            
        if ssid != None:
            
            #Query the database to find the ssid
            cur = conn.cursor()
            cur.execute("Select id from ssid where name = %s",(ssid,))
            r = cur.fetchone()
            if r == None:
                cur.execute("Insert into ssid (name) VALUES(%s) returning id;",(ssid,))
                r = cur.fetchone()
                ssuid, = r
                cur.close()    
                conn.commit()
            else:
                ssuid, = r
                cur.close()
                conn.rollback()
        else:
            ssuid = None
            
        #Query the database for a beacon/probe by the station
        #if it was observed in the past 5 minutes,
        #don't add this one to the database                
        cur = conn.cursor()
        
        if isBeacon:
            cur.execute("Insert into beacon (station,ssid,seen) VALUES(%s,%s,current_timestamp at time zone 'utc')",(suid,ssuid,))
            cur.close()
            conn.commit()
        elif isProbe:
            cur.execute("Insert into probe(station,ssid,seen) VALUES(%s,%s,current_timestamp at time zone 'utc')",(suid,ssuid,))
            cur.close()
            conn.commit()
        
if __name__ == "__main__":
    iface = 'wlan0'
    try:
        handler = Handler()                
        sniff(iface=iface,prn=handler,store=0)
    except Exception, msg:
        print msg
        sys.exit(0)
