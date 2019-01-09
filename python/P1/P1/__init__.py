import re
from PyCRC.CRC16 import CRC16
import serial
from time import sleep

# Constants
EOT_CHAR = '!'  # End of transmission character
TELEGRAM_LENGTH = 40  # lines
OBIS = [
    ['Energy import [low]', '1-0:1.8.1', r'(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)'],
    ['Energy import [high]', '1-0:1.8.2', r'(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)'],
    ['Energy export [low]', '1-0:2.8.1', r'(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)'],
    ['Energy export [high]', '1-0:2.8.2', r'(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)'],
    ['Power import', '1-0:1.7.0', r'(\d-\d):(\d\.?)+\((\d{2}\.\d{3})\*kW\)'],
    ['Power export', '1-0:2.7.0', r'(\d-\d):(\d\.?)+\((\d{2}\.\d{3})\*kW\)']
]


class Client:

    def __init__(self, port):
        # Serial port configuration
        self.ser = serial.Serial()
        self.ser.port = port
        self.ser.baudrate = 115200
        self.ser.parity = serial.PARITY_NONE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.stopbits = serial.STOPBITS_ONE

        # P1 configuration
        self.telegram = []
        self.crc_data = ''

        # Logger configuration
        self.logger = None

        # Initialise local variables
        self.power = 0.0
        self.energy = 0.0
        self.retries = 3
        self.retry_delay = 10

    def attach_logger(self, logger):
        self.logger = logger

    def open_port(self):
        try:
            self.ser.open()
        except serial.SerialException as e:
            if self.logger:
                self.logger.error('Failed to open serial port \'%s\' [\'%s\'' % (self.ser.port, str(e)))
            return False
        else:
            return True

    def close_port(self):
        self.ser.close()

    def read_line(self):
        line = self.ser.readline().decode('ascii')
        return line

    def add_line_to_telegram(self, line):
        self.telegram.append(line.strip())
        if not line.startswith('!'):
            self.crc_data += line

    def new_telegram(self):
        self.telegram.clear()
        self.crc_data = ''

    def verify_crc(self):
        # Get received CRC from last last of telegram
        crc_received = self.telegram[len(self.telegram)-1][1:]  # Remove EOT_CHAR from received CRC
        # Compute CRC from received data
        crc = "0x{:04x}".format(CRC16().calculate(self.crc_data+'!'))
        crc = crc[2:].upper()
        # Return verified CRC
        return crc == crc_received

    def process_telegram(self):
        # Reset power and energy variables
        self.power = 0.0
        self.energy = 0.0

        # Extract power and energy values
        for line in range(1, len(self.telegram)):
            for desc, ref, regex in OBIS:
                if self.telegram[line].startswith(ref):
                    m = re.search(regex, self.telegram[line])
                    if self.telegram[line].startswith('1-0:1.8'):
                        self.energy += float(m.group(3))*1000               # kWh => Wh
                    elif self.telegram[line].startswith('1-0:2.8'):
                        self.energy -= float(m.group(3))*1000               # kWh => Wh
                    elif self.telegram[line].startswith('1-0:1.7'):
                        self.power += float(m.group(3))*1000                # kW => W
                    elif self.telegram[line].startswith('1-0:2.7'):
                        self.power -= float(m.group(3))*1000                # kW => W

    def read_telegram(self):
        # Open serial port
        for itt in range(1, self.retries):
            if self.open_port():
                # Start receiving data
                line = self.read_line()

                # Find start of transmission [first line starts with '/']
                line_no = 0
                while not line.startswith('/'):
                    line = self.read_line()

                # Start of transmission detected
                self.new_telegram()
                self.add_line_to_telegram(line)

                # Read until end of telegram character detected
                while not line.startswith(EOT_CHAR):
                    line = self.read_line()
                    self.add_line_to_telegram(line)

                # Complete telegram received close port
                self.close_port()

                # Verify CRC
                if self.verify_crc():
                    self.process_telegram()
                    return True
            else:
                sleep(self.retry_delay)

        # Failed to read after self.retries retries
        return False
