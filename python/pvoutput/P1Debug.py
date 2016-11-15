import serial

# Serial port configuration
port = '/dev/ttyACM0'
baudrate = '115200'

# Initialize variables
ser = serial.Serial(port, baudrate)

while(True):
    data = str(ser.readline())
    print(data)
