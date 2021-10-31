# sensor-service
Simple Python daemon for reading 1-wire sensors and logging to a InfluxDB.
Graphs can later be created with Grafana.

## Settings

The following environment-variables is used to configure the service:

- INFLUXDB_HOST - hostname to InfluxDb server
- INFLUXDB_USER - username to InfluxDb server
- INFLUXDB_PASSWD - password to InfluxDb server
- INFLUXDB_DB - database on InfluxDB server that should be used. Must be created first with "create database <name>"
- OWSERVER_HOST - hostname to Owserver 

## Docker
  
Build image with `docker build -t sensor-service .`
  
Run container with `docker run --privileged -e INFLUXDB_HOST=localhost -e INFLUXDB_USER=myuser sensor-service:latest`

