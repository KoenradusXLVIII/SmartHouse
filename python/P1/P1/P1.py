import re
import sys
from PyCRC.CRC16 import CRC16
import serial

# Constants
EOT_CHAR = '!'  # End of transmission character
TELEGRAM_LENGTH = 23  # lines
OBIS = [
    ['Energy import [low]', '1-0:1.8.1', '(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)'],
    ['Energy import [high]', '1-0:1.8.2', '(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)'],
    ['Energy export [low]', '1-0:2.8.1', '(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)'],
    ['Energy export [high]', '1-0:2.8.2', '(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)'],
    ['Power import', '1-0:1.7.0', '(\d-\d):(\d\.?)+\((\d{2}\.\d{3})\*kW\)'],
    ['Power export', '1-0:2.7.0', '(\d-\d):(\d\.?)+\((\d{2}\.\d{3})\*kW\)']
]


class Client:

    def __init__(self, port, serial_no):
        # Serial port configuration
        self.ser = serial.Serial()
        self.ser.port = port
        self.ser.baudrate = 115200
        self.ser.parity = 'N'
        self.ser.bytesize = 8
        self.ser.stopbits = 1

        # P1 configuration
        self.serial_no = serial_no
        self.telegram = ''
        self.crc_data = ''

        # Logger configuration
        self.logger = None

        # Initialise local variables
        self.power = 0.0
        self.energy = 0.0

    def attach_logger(self, logger):
        self.logger = logger

    def open_port(self):
        if not self.ser.isOpen():
            try:
                self.ser.open()
                if self.logger:
                    self.logger.debug('Opened serial port \'%s\'' % self.port)
                return True
            except serial.SerialException:
                if self.logger:
                    self.logger.error('Failed to open serial port \'%s\'' % self.port)
                return False
        else:
            if self.logger:
                self.logger.debug('Tried to open port \'%s\', but it was already open' % self.port)

    def close_port(self):
        if self.ser.isOpen():
            self.ser.close()
            if self.logger:
                self.logger.debug('Closed serial port \'%s\'' % self.port)
        else:
            if self.logger:
                self.logger.debug('Tried to close port \'%s\', but it was already closed' % self.port)

    def read_line(self):
        if self.ser.isOpen():
            return str(self.ser.readline())

    def add_line_to_telegram(self, line, add_to_crc='True'):
        self.telegram.append(line.strip())
        if add_to_crc:
            self.crc_data += line

    def new_telegram(self):
        self.telegram = ''
        self.crc_data = ''

    def verify_crc(self):
        # Add EOT_CHAR to CRC data
        self.crc_data += '!'
        # Get received CRC from last last of telegram
        crc_received = self.telegram[len(self.telegram)-1][1:] # Remove EOT_CHAR from received CRC
        # Compute CRC from received data
        crc = "0x{:04x}".format(CRC16().calculate(self.crc_data))
        crc = crc[2:].upper()
        # Verify received CRC matches data
        if crc == crc_received:
            if self.logger:
                self.logger.debug('Valid data, CRC match: 0x%s' % crc)
            return True
        else:
            if self.logger:
                self.logger.debug('CRC mismatch: 0x%s / 0x%s' % (crc, crc_received))
            return False

    def process_telegram(self):
        # Reset power and energy variables
        self.power = 0.0
        self.energy = 0.0

        # Extract power and energy values
        for line in range(1,len(self.telegram)):
            for desc, ref, regex in OBIS:
                if self.telegram[line].startswith(ref):
                    m = re.search(regex, self.telegram[line])
                    if self.telegram[line].startswith('1-0:1.8'):
                        self.energy += float(m.group(3))
                    elif self.telegram[line].startswith('1-0:2.8'):
                        self.energy -= float(m.group(3))
                    elif self.telegram[line].startswith('1-0:1.7'):
                        self.power += float(m.group(3))
                    elif self.telegram[line].startswith('1-0:2.7'):
                        self.power -= float(m.group(3))

        # Convert from kW(h) to W(h)
        self.power *= 1000.0
        self.energy *= 1000.0

    def get_power(self):
        return self.power

    def get_energy(self):
        return self.energy

    def read_telegram(self):
        itt = 0

        # Open serial port
        if self.open_port():
            # Start receiving data
            line = self.read_line()

            # Find start of transmission [serial number]
            while self.serial_no not in line:
                line = self.read_line()
                itt += 1
                if itt >= TELEGRAM_LENGTH:
                    if self.logger:
                        self.logger.error('Invalid telegram [serial number not found]')
                        return False

            # Start of transmission detected
            self.new_telegram()
            self.add_line_to_telegram(line)
            if self.logger:
                self.logger.debug('[P1]: %s' % line.strip())

            # Read until end of telegram character detected
            while not line.startswith(EOT_CHAR):
                line = self.read_line()
                if not line.startswith(EOT_CHAR):
                    self.add_line_to_telegram(line)
                else:
                    # Do not add line with EOT char to CRC
                    self.add_line_to_telegram(line, False)

            # Verify CRC
            if self.verify_crc():
                self.process_telegram()


