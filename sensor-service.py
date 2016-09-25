#!/usr/bin/env python

import sys, time
import RPi.GPIO as GPIO
import pyownet
from influxdb import InfluxDBClient
from daemon import Daemon

class MyDaemon(Daemon):
	def run(self):

		# change this to the pin used to monitor the rain sensor
		rain_sensor_pin = 23
		# database engine host
		host='localhost'
		# database engine port
		port = 8086
		# database engine user
		user = "root"
		# database engine password
		password = "root"
		# database to save all our logging to
		db_name = "sensors"

		print 'Starting sensor daemon.'
		# setup raspberry pi pins
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(rain_sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		# setup influx database engine connection and sensor database 
		db = InfluxDBClient(host, port, user, password, db_name)

		# function to be called when it's raining 
		def rain_trigger_callback(channel):
			print 'The Rain Keeps Pouring Down. ' + time.strftime('%a, %d %b %Y %H:%M:%S %Z(%z)')
			# setup values to save to the database. database will add timestamp automatically
			json_body = [
    			{
        			"measurement": "rain",
        			"tags": {},
        			"fields": {
            				"value": 1.0
        			}
    			}]
			# save to database
			db.write_points(json_body)

		# register callback for rising-edge interrupt on rain sensor pin, and add a debounce time of 1000 ms.
		GPIO.add_event_detect(rain_sensor_pin, GPIO.RISING, callback=rain_trigger_callback, bouncetime=1000)  

		try:
			# setup owserver(1-wire) connection
			owproxy = pyownet.protocol.proxy(host='localhost', port=4304, flags=0, persistent=False, verbose=False)
			# get list of all available 1-wire sensors, but only the sensors that starts with family name = 10 (DS1820)
			owdevices = [d for d in owproxy.dir() if '10.' in d]
			print 'Found owdevices: ' + str(owdevices)

			# loop until program exists
			while True:
				# loop found 1-wire devices
				for id in owdevices:
					# remove '/' in 1-wire device names, we don't need them
					id = id.replace('/', '')
					# read temperature from one sensor, convert reading to a float-value
					temp = float(owproxy.read('/{0}/temperature'.format(id)))
					print 'Read temperature: {0} from device: {1}'.format(temp, id)
					# setup values to save to the database. database will add timestamp automatically
        				json_body = [
        				{
                				"measurement": "temperature",
                				"tags": { 
							"sensor": id
						},
                				"fields": {
                        				"value": temp
                				}
        				}]
					# save to database
        				db.write_points(json_body)

				# wait 600 seconds(10 minutes) before we read sensors again
				time.sleep(600)
	
		except pyownet.protocol.Error as err:
        		log = open('/var/log/sensor-service/error.log', 'w')
        		log.write('Something went wrong: {}'.format(err))
        		log.close()
			GPIO.cleanup()
		except KeyboardInterrupt:  
			GPIO.cleanup()

if __name__ == "__main__":
	daemon = MyDaemon('/var/run/sensor-service.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		else:
			print "Unknown command"
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart" % sys.argv[0]
		sys.exit(2)

