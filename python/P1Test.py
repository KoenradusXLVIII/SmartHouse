import serial

port = '/dev/ttyACM0'
baudrate = '115200'

ser = serial.Serial(port, baudrate)
while True:
    data = ser.readline()
    print(data)
