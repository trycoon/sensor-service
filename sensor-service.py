#!/usr/bin/env python

import sys, time, os
import logging
import RPi.GPIO as GPIO
import pyownet
from influxdb import InfluxDBClient


# change this to the pin used to monitor the rain sensor
rain_sensor_pin = 4
# database engine host
host = os.getenv('INFLUXDB_HOST', 'localhost')
# database engine port
port = 8086
# database engine user
user = os.getenv('INFLUXDB_USER', 'admin')
# database engine password
password = os.getenv('INFLUXDB_PASSWD', 'admin')
# database to save all our logging to
db_name = os.getenv('INFLUXDB_DB', 'sensors')

logging.basicConfig( filename="/var/log/sensor-service.log",
                     filemode='w',
                     level=logging.DEBUG,
                     format= '%(asctime)s - %(levelname)s - %(message)s',
                   )

logger=logging.getLogger(__name__)

logging.info('Starting sensor daemon.')
# setup raspberry pi pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(rain_sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# setup influx database engine connection and sensor database 
db = InfluxDBClient(host, port, user, password, db_name)

# function to be called when it's raining 
def rain_trigger_callback(channel):
	logger.info('The Rain Keeps Pouring Down. %s', time.strftime('%a, %d %b %Y %H:%M:%S %Z(%z)'))
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
	try:
		db.write_points(json_body)
	except Exception as err:
		logger.error('Failed to log rainsensor reading to database. %s', err, exc_info=True)

# register callback for rising-edge interrupt on rain sensor pin, and add a debounce time of 1000 ms.
GPIO.add_event_detect(rain_sensor_pin, GPIO.RISING, callback=rain_trigger_callback, bouncetime=1000)  

try:
	# setup owserver(1-wire) connection
	owproxy = pyownet.protocol.proxy(host=os.getenv('OWSERVER_HOST', 'localhost'), port=4304, flags=0, persistent=False, verbose=False)
	# get list of all available 1-wire sensors, but only the sensors that starts with family name = 10 (DS1820)
	owdevices = [d for d in owproxy.dir() if '10.' in d]
	logger.info('Found owdevices: %s', str(owdevices))

	# loop until program exists
	while True:
		# loop found 1-wire devices
		for id in owdevices:
			# remove '/' in 1-wire device names, we don't need them
			id = id.replace('/', '')
			# read temperature from one sensor, convert reading to a float-value
			temp = float(owproxy.read('/{0}/temperature'.format(id)))
			logger.info('Read temperature: {0} from device: {1}'.format(temp, id))
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
			try:
        			db.write_points(json_body)
			except Exception as err:
				logger.error('Failed to log temperature readings to database. %s', err, exc_info=True) 

		# wait 600 seconds(10 minutes) before we read sensors again
		time.sleep(600)
	
except pyownet.protocol.Error as err:
	logger.error('Failed to read from Owserver. %s', err, exc_info=True)
	GPIO.cleanup()
except KeyboardInterrupt:  
	GPIO.cleanup()
