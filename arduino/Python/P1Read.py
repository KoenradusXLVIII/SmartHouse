import serial

port = '/dev/ttyACM0'
baudrate = '9600'

ser = serial.Serial(port, baudrate)
while True:
    data = ser.readline()
    print(data)
