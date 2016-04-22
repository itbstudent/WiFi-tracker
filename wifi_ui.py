from PyQt4 import QtGui, QtCore 	#QtGui - imports GUI; Qtcore - imports event handling (to make buttons do things)
import wifi_mon
import logging
from wifi_mon import deauth
from PyQt4.Qt import QWebView, QUrl
from wigle import Wigle, WigleRatelimitExceeded
from Outlog import OutLog
logging.getLogger("scapy.runtime").setLevel(logging.ERROR) # Shut up Scapy
from scapy.all import *
conf.verb = 0 # Scapy I thought I told you to shut up
from subprocess import call
import probe_scan
import psycopg2
import manuf
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

class Window(QtGui.QMainWindow):				#Application inherit from QtGui.QMainWindow (also QWidget can be used); Window is an object

	# ===== Window ===== 

	def __init__(self):					#Defines Window (init method); from now, 'self' will reference to the window; 
								#everytime a window object is made the init method runs; Core of the application is in __init__
		super(Window, self).__init__()				#Super returnd parent object (which is QMainWindow);  () - Empty parameter
		self.setGeometry(50, 50, 1050, 650)			#Set the geometry of the window. (starting X; starting Y; width; length)
		self.setWindowTitle("Wifi Probe Scanner Project")		#Set title of the window (Window name)
		self.setWindowIcon(QtGui.QIcon('itb.png'))		#Set the image in the window name (doesn't seem to work in Linux)
		
		pic = QtGui.QLabel(self)
		pic.setGeometry(505,45,520,520)
		#use full ABSOLUTE path to the image, not relative
		pic.setPixmap(QtGui.QPixmap(os.getcwd() + "/python.jpg"))
		frame = QtGui.QGroupBox(self)    
		frame.setTitle("Google Map")
		frame.setGeometry(500,40,515,515)
		
		console = QtGui.QTextEdit(self)
		#console.setTitle("Console output")
		console.setGeometry (25,400,450,200)
		sys.stdout = OutLog(console,sys.stdout)
		sys.stderr = OutLog(console,sys.stderr, QtGui.QColor(255,0,0))
		
		
	# ===== Main Menu ===== 
									#Menu Choices
		monitorMode = QtGui.QAction("& Enable Monitor Mode", self)	#Defines action for Wi-Fi Monitor Mode
		monitorMode.setShortcut("Ctrl+M")			#Sets shortcut for Wi-Fi monitor mode action
		monitorMode.setStatusTip("Wi-Fi Monitor Mode")		#Information shown in the status bar (doesn't work in the linux)
		monitorMode.triggered.connect(self.wifi_monitor)	#Calls the method for enabling Wi-Fi monitor mode

		launchScan = QtGui.QAction("& Launch Probe Scan", self)	#Defines action for Scanning Probes
		launchScan.setShortcut("Ctrl+P")			#Sets shortcut for action
		launchScan.setStatusTip("Start Wi-Fi Scan")		#Information shown in the status bar (doesn't work in the linux)
		launchScan.triggered.connect(self.probe_scan)		#Calls the method for scanning probes

		quitAction = QtGui.QAction("& Exit Application", self)	#Defines action
		quitAction.setShortcut("Ctrl+Q")			#Sets shortcut for action
		quitAction.setStatusTip("Terminate the Application")	#Information shown in the status bar (doesn't work in the linux)
		quitAction.triggered.connect(self.close_application)	#Calls the method for closing the application
		
		cleardb = QtGui.QAction("& Clear database from records", self)	#Defines action for truncating tables
		cleardb.setShortcut("Ctrl+F")			#Sets shortcut for action
		cleardb.setStatusTip("Clear database")		#Information shown in the status bar 
		cleardb.triggered.connect(self.clear_db)		#Calls the method for truncating tables
		
		plotMap = QtGui.QAction("& Generate maps from probes", self)	#Defines action for Plotting maps
		plotMap.setShortcut("Ctrl+G")			#Sets shortcut for action
		plotMap.setStatusTip("Generate maps")		#Information shown in the status bar 
		plotMap.triggered.connect(self.getCoordinates)		#Calls the method for generating html
		
		updmanuf = QtGui.QAction("& Update oui file", self)	#Defines action for truncating tables
		updmanuf.setShortcut("Ctrl+M")			#Sets shortcut for action
		updmanuf.setStatusTip("Update oui file")		#Information shown in the status bar 
		updmanuf.triggered.connect(self.manufUpdate)		#Calls the method for truncating tables
		
		disable = QtGui.QAction("& Disable Monitor mode", self)	#Defines action for disabling monitor mode 
		disable.setShortcut("Ctrl+D")			#Sets shortcut for action
		disable.setStatusTip("Disabling monitor mode")		#Information shown in the status bar 
		disable.triggered.connect(self.disable_monitor)		#Calls the method for disabling monitor mode
		
		deauthall = QtGui.QAction("& Deauthenticate all", self)	#Defines action for deauthenticating all devices around 
		deauthall.setShortcut("Ctrl+Z")			#Sets shortcut for action
		deauthall.setStatusTip("Deauthenticate all")		#Information shown in the status bar 
		deauthall.triggered.connect(self.deauth_all)		#Calls the method for deauthenticating all devices around
		
		showgoogle = QtGui.QAction("& Show Google Map", self)	#Defines action for deauthenticating all devices around 
		showgoogle.setShortcut("Ctrl+G")			#Sets shortcut for action
		showgoogle.setStatusTip("Show Google Map")		#Information shown in the status bar 
		showgoogle.triggered.connect(self.deauth_all)		#Calls the method for deauthenticating all devices around
		
		
		self.statusBar()					#Calls the status bar (to show setStatusTip), nothing else is needed!
		
									#Main Menu
									
		mainMenu = self.menuBar()				#menuBar object is assigned to mainMenu, because we will need to modify it/add to it
		fileMenu = mainMenu.addMenu('&Menu')			#Defines one line of menu and assigned it a name
		fileMenu.addAction(monitorMode)				#Adds action to the menu line - Wi-Fi Monitor Mode
		fileMenu.addAction(launchScan)				#Adds action to the menu line - Scanning Probes
		fileMenu.addAction(plotMap)				#Adds action to the menu line - get coordinates and generate map	
		fileMenu.addAction(disable)				#Adds action to the menu line - disable wifi 	
		fileMenu.addAction(showgoogle)			#Adds action to the menu line - show map
		fileMenu.addAction(quitAction)				#Adds action to the menu line - Exit Application	
		
		fileMenu2 = mainMenu.addMenu('&Options')
		fileMenu2.addAction(cleardb)				#Adds action to the menu line - Clear DB
		fileMenu2.addAction(updmanuf)				#Adds action to the menu line - Clear DB
		fileMenu2.addAction(deauthall)				#Adds action to the menu line - Clear DB
		
		
		self.home()						#Refers to the next method


	# ===== Main Window ===== 

	def home(self):							#Defines a method 'home' 

									#Button for Wi-Fi Monitor Mode
		btn1 = QtGui.QPushButton("Enable Monitor Mode", self)	#Defines a button with parameter name (!!! WHY PASS SELF ???)
		btn1.clicked.connect(self.wifi_monitor)			#Defines an event (through .connect), event is Monitor Mode
		btn1.resize(180, 40)					#Defines the size of the button (width; length) or PyQt suggest minimum size btn1.minimumSizeHint()
		btn1.move(25, 50)					#Defines location of the button on the screen (starting X; starting Y)
		btn1.setStyleSheet("QPushButton { background-color: None }"
						   "QPushButton:pressed { background-color: green }")							
									#Button for Scanning Probes
		#self.progress = QtGui.QProgressBar(self)
		#self.progress.setGeometry(50, 620, 1100, 20)
		
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
		btn4.clicked.connect(self.disable_monitor)			#Defines an event (through .connect), event is Monitor Mode
		btn4.resize(180, 40)					#Defines the size of the button (width; length) or PyQt suggest minimum size btn1.minimumSizeHint()
		btn4.move(25, 190)					#Defines location of the button on the screen (starting X; starting Y)

		btn5 = QtGui.QPushButton("Get coordinates", self)	#Defines a button with parameter name (!!! WHY PASS SELF ???)
		btn5.clicked.connect(self.getCoordinates)			#Defines an event (through .connect), event is Monitor Mode
		btn5.resize(180, 40)					#Defines the size of the button (width; length) or PyQt suggest minimum size btn1.minimumSizeHint()
		btn5.move(25, 260)					#Defines location of the button on the screen (starting X; starting Y)
		
		btn6 = QtGui.QPushButton("DEAUTH", self)	#Defines a button with parameter name
		btn6.clicked.connect(self.deauth_all)			#Defines an event (through .connect), event is Scanning Probes
		btn6.resize(200, 40)					#Defines the size of the button (width; length)
		btn6.move(250, 330)					#Defines location of the button on the screen (starting X; starting Y)
		btn6.setStyleSheet("background-color: red")
		
		btn7 = QtGui.QPushButton("Show google map", self)	#Defines a button with parameter name
		btn7.clicked.connect(self.deauth_all)			#Defines an event (through .connect), event is Scanning Probes
		btn7.resize(500, 40)					#Defines the size of the button (width; length)
		btn7.move(500, 560)					#Defines location of the button on the screen (starting X; starting Y)
		btn7.setStyleSheet("background-color: green")
		
		
											#Style Choice (the GUI part)
		#print(self.style().objectName())			#Prints out what is default style
		styleChoice = QtGui.QLabel("Choose device", self)	#Defines the style object with parameter (Name) -> Its the label saying what it is
		comboBox = QtGui.QComboBox(self)			#QComBox is/means drop down button, defines dropdown object
		dropdown = self.getStations()
		for item in dropdown:
			comboBox.addItem (str(item))				#This was a test style, doesn't do anything, but it doesn't break the app!
		comboBox.resize(200,20)
		comboBox.move(250, 50)					#Defines location of the box on the screen (starting X; starting Y)
		styleChoice.move(250, 25)				#Defines location of the style choice on the screen (starting X; starting Y)
		comboBox.activated[str].connect(self.style_choice)	#Activate and display the default/current style/value and connect it to method style_choice
		
		
		self.show()						#Shows the application in the end (call the graphics from memory and display it)


	# ===== Methods ===== 
	
	def style_choice(self, text):					#Defines the method of the style choice (the 'Doing something' with the choice)...
									# & pass self and text parameter
		self.styleChoice.setText(text)				# set the style to QStyleFactory setText to text (to the lable saying what it is)
		QtGui.QApplication.setStyle(QtGui.QStyleFactory.create(text)) #Set the style of the GUI to text, aka the QStyleFactory types (motif, windows, cde..)
		
		
	def wifi_monitor(self):						#Method for closing application
		try:
			wifi_mon.start_mon_mode(iface)
			QtGui.QMessageBox.information(self, "Enabling Monitor Mode", "Monitor mode started on strongest interface %s"% (iface))
		except Exception, msg:
			QtGui.QMessageBox.information(self, "Enabling Monitor Mode", "Enabling monitor mode failed due to error: %s" % (msg,))
	
	def probe_scan(self):						#Method for closing application
		choice = QtGui.QMessageBox.question(self, "Start sniffing", "Start collecting probes on interface %s?"% (iface), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
		if choice == QtGui.QMessageBox.Yes:			#if/else statement - if yes
			print("Starting probes collection")	#Sends a message before quiting (in cmd & loggs)
			#self.completed = 0
			#while self.completed < 100:
			#	self.completed += 0.0001
			#	self.progress.setValue(self.completed)
			handler = probe_scan.Handler()                
			sniff = probe_scan.sniff(iface=iface,prn=handler,store=0,timeout=300)
			self.comboBox.clear()
			self.comboBox.update()
		else:							#if/else statement - else (No)
			pass						#pass - nothing happens
	
	def deauth_all(self):						#Method for closing application
		choice = QtGui.QMessageBox.question(self, "Deauth all devices", "Are you completely sure that you want to do it?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
		if choice == QtGui.QMessageBox.Yes:			#if/else statement - if yes
			try:
				channels = range(1,14)
				for channel in channels:
					deauth(channel) 
				QtGui.QMessageBox.information(self, "Deauth", "Deauth started")
			except Exception, msg:
				QtGui.QMessageBox.information(self, "Enabling Monitor Mode", "Enabling monitor mode failed due to error: %s" % (msg,))
		else:							#if/else statement - else (No)
			pass						#pass - nothing happens
	
	def getStations(self):
		con = psycopg2.connect(database='wifi', user='probecap', host = 'localhost', password='pass')
		con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
		cur = con.cursor()
		try:
			cur.execute("""select distinct s.model from station s where s.lastseen > current_timestamp at time zone 'utc' - (30 * interval '1 minutes');""")
			stations = [item[0] for item in cur.fetchall()]
		except psycopg2.DatabaseError, e:
			print 'Error %s' % e    
		return stations
	
	def getCoordinates(self):
		con = psycopg2.connect(database='wifi', user='probecap', host = 'localhost', password='pass')
		con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
		cur = con.cursor()
		try:
			cur.execute("""select s.name from probe p join ssid s on p.ssid = s.id join station st on p.station = st.id where st.model = 'Apple';""")
			data = cur.fetchall()
			for item in data:
				print item
				#result = os.system("wigle_search --user Gvozdik --pass jaho4u4aju --ssid %s", *item)
				#print result 
				try:
					results = Wigle('user789', '12345').search(
		            ssid=item,
		            max_results=100)
					for result in results:
						print("%(ssid)s, %(trilat)s, %(trilong)s" % result)
				except WigleRatelimitExceeded:
					print("Cannot query Wigle - exceeded number of allowed requests")
				#cred = Wigle('itbstudent', 'p@SSW0RD')
				#data = cred.search(ssid='row')
				
		except psycopg2.DatabaseError, e:
			print 'Error %s' % e    
			
	def showMap(self):
		web_page = QWebView(self)
		web_page.setGeometry(650,50,500,500)
		web_page.load(QUrl("file:///var/www/html/mymap7.html"))
		web_page.show()									
		
	def close_application(self):					#Method for closing application
										#Pop up question box with yes/no option; parameters: self, Wwindow title, Question, Yes or No
		choice = QtGui.QMessageBox.question(self, "Exit Application", "Do you want to exit the application?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
		if choice == QtGui.QMessageBox.Yes:			#if/else statement - if yes
			sys.exit()					#Exit everything				
		else:							#if/else statement - else (No)
			pass		
						#pass - nothing happens
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
			cur.execute('TRUNCATE TABLE station, ssid, probe;')
			QtGui.QMessageBox.information(self, "Clearing Database", "Tables truncated")
		except psycopg2.DatabaseError, e:
			print 'Error %s' % e    
		cur.close()
		con.close()
		
	def manufUpdate(self):
		try:
			updateoui = manuf.MacParser()
			updateoui.refresh()
			QtGui.QMessageBox.information(self, "Updating oui file", "OUI Database file is updated")
		except Exception, msg:
			print msg

			
monitors, interfaces = wifi_mon.iwconfig()
iface = wifi_mon.get_iface(interfaces)
						# NO DESCRIPTION - This runs a window object (details of the object are above)

def run():							# Main Running Method (Function) - run()
	if os.geteuid():
		sys.exit('Please run as root')
	app = QtGui.QApplication(sys.argv)			# App definition (defines application); sys.argv allows to call
	GUI = Window()
	sys.exit(app.exec_())					# NO DESCRIPTION

run()								#Call 'run' to run code


# ___Notes___
#
#  If the method belongsto PyQT, it has 'Q' in front of it, like btn = QtGui.QPushButton
#  If the method belongs to us, it doesn't have a 'Q', like self.home()
