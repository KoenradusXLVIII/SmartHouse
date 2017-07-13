from influxdb import InfluxDBClient

client = InfluxDBClient('localhost', 8086, 'root', 'root', 'SmartHouse')

result = client.query('select * from solar_power;')

for value in result:
    print('Result: %s' % value[0]['value'])
