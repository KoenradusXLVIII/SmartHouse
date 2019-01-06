# Python3

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
        self.ser.parity = 'N'
        self.ser.bytesize = 8
        self.ser.stopbits = 1

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
        if not self.ser.isOpen():
            try:
                self.ser.open()
                if self.logger:
                    self.logger.debug('Opened serial port \'%s\'' % self.ser.port)
                return True
            except serial.SerialException:
                if self.logger:
                    self.logger.error('Failed to open serial port \'%s\'' % self.ser.port)
                return False
        else:
            if self.logger:
                self.logger.debug('Tried to open port \'%s\', but it was already open' % self.ser.port)

    def close_port(self):
        if self.ser.isOpen():
            self.ser.close()
            if self.logger:
                self.logger.debug('Closed serial port \'%s\'' % self.ser.port)
        else:
            if self.logger:
                self.logger.debug('Tried to close port \'%s\', but it was already closed' % self.ser.port)

    def read_line(self):
        if self.ser.isOpen():
            line = self.ser.readline().decode('utf-8')
            if self.logger:
                self.logger.debug('[P1]: %s' % line.strip())
            return str(line)

    def add_line_to_telegram(self, line, add_to_crc=True):
        self.telegram.append(line.strip())
        if add_to_crc:
            self.crc_data += line

    def new_telegram(self):
        self.telegram = []
        self.crc_data = ''

    def verify_crc(self):
        # Add EOT_CHAR to CRC data
        self.crc_data += '!'
        # Get received CRC from last last of telegram
        crc_received = self.telegram[len(self.telegram)-1][1:]  # Remove EOT_CHAR from received CRC
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
        for line in range(1, len(self.telegram)):
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

    def read_telegram(self):

        # Open serial port
        for itt in range(1, self.retries):
            if self.logger:
                self.logger.debug('Starting P1 iteration %d' % itt)
            if self.open_port():
                # Start receiving data
                line = self.read_line()

                # Find start of transmission [first line starts with '/']
                line_no = 0
                while not line.startswith('/'):
                    line = self.read_line()
                    line_no += 1
                    if line_no >= TELEGRAM_LENGTH:
                        self.close_port()
                        break

                if line_no >= TELEGRAM_LENGTH:
                    if self.logger:
                        self.logger.info('Invalid telegram [serial number not found]')
                else:
                    # Start of transmission detected
                    self.logger.debug('Valid telegram [found after %d lines read]' % line_no)
                    self.new_telegram()
                    self.add_line_to_telegram(line)

                    # Read until end of telegram character detected
                    while not line.startswith(EOT_CHAR):
                        line = self.read_line()
                        if not line.startswith(EOT_CHAR):
                            self.add_line_to_telegram(line)
                        else:
                            # Do not add line with EOT char to CRC
                            self.add_line_to_telegram(line, False)
                    self.close_port()

                    # Verify CRC
                    if self.verify_crc():
                        self.process_telegram()
                        return True
            else:
                sleep(self.retry_delay)

        # Failed to read after self.retries retries
        return False
