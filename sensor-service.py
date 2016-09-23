#!/usr/bin/env python

import sys, time
import RPi.GPIO as GPIO
import pyownet
from influxdb import InfluxDBClient
from daemon import Daemon

# change this to the pin used to monitor the rain sensor
rain_sensor_pin = 23
host='localhost'
port = 8086
user = "root"
password = "root"
db_name = "sensors"

print 'Starting sensor daemon.'
GPIO.setmode(GPIO.BCM)
GPIO.setup(rain_sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def rain_trigger_callback(channel):
	print 'The Rain Keeps Pouring Down. ' + time.strftime('%a, %d %b %Y %H:%M:%S %Z(%z)')

# setup influx database engine connection and sensor database 
db = InfluxDBClient(host, port, user, password, db_name)

# register callback for rising-edge interrupt on rain sensor pin, and a debounce time of 500 ms.
GPIO.add_event_detect(rain_sensor_pin, GPIO.RISING, callback=rain_trigger_callback, bouncetime=500)  

try:
	# setup owserver connection
	owproxy = pyownet.protocol.proxy(host='localhost', port=4304, flags=0, persistent=False, verbose=False)
	# get list of all available 1-wire sensors, but only the sensors that starts with family name = 10 (DS1820)
	owdevices = [d for d in owproxy.dir() if '10.' in d]
	print 'Found owdevices: ' + str(owdevices)

	while True:
		#owproxy.read()
		#db.write_points_with_precision([{"points":[[1400000000000,1,1,1]], "name":"foo", "columns":["time", "a","b","c"]}], time_precision='u')
		# sample temperature every 600 seconds(10 minutes)
		time.sleep(600)
	
except pyownet.protocol.Error as err:
        log = open('/home/pi/christer-service/error.log', 'w')
        log.write('Something went wrong: {}'.format(err))
        log.close()
	GPIO.cleanup()
except KeyboardInterrupt:  
	GPIO.cleanup()


#class MyDaemon(Daemon):
#	def run(self):
#	        # Setup rain-sensor input.
#		print "Starting sensor service."	
#		GPIO.setmode(GPIO.BCM)
#		GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#
#		try:
#			# setup owserver connection
#			owproxy = pyownet.protocol.proxy(host='localhost', port=4304, flags=0, persistent=False, verbose=False)
#		        print "Got connection to owserver."	
#			devices = owproxy.dir()
#	               
#			while True:
 #       	        	GPIO.wait_for_edge(23, GPIO.FALLING)
#				time.sleep(0.5)
#		except pyownet.protocol.Error as err:
#			log = open('/home/pi/christer-service/error.log', 'w')
#			log.write('Something went wrong: {}'.format(err))
#			log.close()
#		GPIO.cleanup()
#
#if __name__ == "__main__":
#	daemon = MyDaemon('/tmp/christer-service.pid')
#	if len(sys.argv) == 2:
#		if 'start' == sys.argv[1]:
#			daemon.start()
#		elif 'stop' == sys.argv[1]:
#			daemon.stop()
#		elif 'restart' == sys.argv[1]:
#			daemon.restart()
#		else:
#			print "Unknown command"
#			sys.exit(2)
#		sys.exit(0)
#	else:
#		print "usage: %s start|stop|restart" % sys.argv[0]
#		sys.exit(2)

