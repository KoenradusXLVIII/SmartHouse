# Public imports
import serial
import json
import os
import time
from serial.tools import list_ports
from PyQt5.QtWidgets import *
from PyQt5 import QtGui

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'Node Configurator'
        self.init()

    def init(self):
        # Scan COM ports
        node_ports = self.scan_ports()

        # Connection elements
        self.gb_connection = QGroupBox("Node Connection")
        self.gb_connection.setStyleSheet("QGroupBox { font-weight: bold; }");
        self.grid_connection = QGridLayout()
        self.label_com_port = QLabel('Select COM port:');
        self.cb_com_ports = QComboBox()
        self.but_connect = QPushButton('Connect')
        self.but_connect.clicked.connect(self.connect_button)
        self.label_uuid_header = QLabel('Node UUID:')
        self.label_uuid_status = QLabel('Not connected')
        for port in node_ports:
            self.cb_com_ports.addItem(port)

        # WiFi status elements
        self.gb_wifi_status = QGroupBox("WiFi Status")
        self.gb_wifi_status.setStyleSheet("QGroupBox { font-weight: bold; }");
        self.gb_wifi_status.setEnabled(False)
        self.grid_wifi_status = QGridLayout()
        self.label_wifi_header = QLabel('Status:')
        self.label_wifi_status = QLabel('');
        self.label_cur_ssid_header = QLabel('SSID:')
        self.label_cur_ssid = QLabel('');
        self.label_IP_header = QLabel('IP:')
        self.label_IP = QLabel('')
        self.but_refresh = QPushButton('Refresh')
        self.but_refresh.clicked.connect(self.get_wifi_status)

        # WiFi configuration elements
        self.gb_wifi = QGroupBox("WiFi Configuration")
        self.gb_wifi.setStyleSheet("QGroupBox { font-weight: bold; }");
        self.gb_wifi.setEnabled(False)
        self.grid_wifi = QGridLayout()
        self.label_ssid = QLabel('Select WiFi network:');
        self.cb_ssids = QComboBox()
        self.label_wifi_pass = QLabel('Enter WiFi password:')
        self.lineedit_wifi_pass = QLineEdit()
        self.lineedit_wifi_pass.setEchoMode(QLineEdit.Password)
        self.progress_upload = QProgressBar(self)
        self.but_upload = QPushButton('Connect')
        self.but_upload.clicked.connect(self.upload_button)
        self.but_reset = QPushButton('Disconnect')
        self.but_reset.clicked.connect(self.reset_button)


        # Create window
        self.setWindowTitle(self.title)
        self.layout = QGridLayout()
        self.setWindowIcon(QtGui.QIcon(os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'icon.png'))

        # Connection groupbox
        self.layout.addWidget(self.gb_connection)
        self.gb_connection.setLayout(self.grid_connection)
        self.grid_connection.addWidget(self.label_com_port, 0, 0)
        self.grid_connection.addWidget(self.cb_com_ports, 0, 1)
        self.grid_connection.addWidget(self.but_connect, 0, 2)
        self.grid_connection.addWidget(self.label_uuid_header, 1, 0)
        self.grid_connection.addWidget(self.label_uuid_status, 1, 1, 1, 2)

        # WiFi Status groupbox
        self.layout.addWidget(self.gb_wifi_status)
        self.gb_wifi_status.setLayout(self.grid_wifi_status)
        self.grid_wifi_status.addWidget(self.label_wifi_header, 0, 0)
        self.grid_wifi_status.addWidget(self.label_wifi_status, 0, 1)
        self.grid_wifi_status.addWidget(self.label_cur_ssid_header, 1, 0)
        self.grid_wifi_status.addWidget(self.label_cur_ssid, 1, 1)
        self.grid_wifi_status.addWidget(self.label_IP_header, 2, 0)
        self.grid_wifi_status.addWidget(self.label_IP, 2, 1)
        self.grid_wifi_status.addWidget(self.but_refresh, 3, 1)

        # WiFi Configuration groupbox
        self.layout.addWidget(self.gb_wifi)
        self.gb_wifi.setLayout(self.grid_wifi)
        self.grid_wifi.addWidget(self.label_ssid, 0, 0)
        self.grid_wifi.addWidget(self.cb_ssids, 0, 1)
        self.grid_wifi.addWidget(self.label_wifi_pass, 1, 0)
        self.grid_wifi.addWidget(self.lineedit_wifi_pass, 1, 1)
        self.grid_wifi.addWidget(self.progress_upload, 2, 0, 1, 2)
        self.grid_wifi.addWidget(self.but_reset, 3, 0)
        self.grid_wifi.addWidget(self.but_upload, 3, 1)

        self.setLayout(self.layout)
        self.resize(300, 10)

    def scan_ports(self):
        # Scan serial port for Arduino(s)
        available_ports = list(list_ports.comports())
        node_ports = []
        for port in available_ports:
            if 'VID:PID=1A86:7523' in port.hwid:
                # This is a Wemos D1 Mini Node
                node_ports.append(port.device)

        return node_ports

    def reset_button(self):
        com_port = str(self.cb_com_ports.currentText())
        try:
            # Open connection
            self.ser = serial.Serial(port=com_port, baudrate=115200)
            self.progress_upload.setValue(0)

            # Reset EEPROM
            self.ser.write('reset\n'.encode())
            ret = self.ser.readline().decode('ascii').strip()

            # Wait for response
            if ret == 'OK':
                time.sleep(1)

            # Close connection
            self.ser.close()

            # Update WiFi Status
            self.get_wifi_status()

        except Exception as e:
            print(e)

        finally:
            # Close connection
            self.ser.close()

    def upload_button(self):
        com_port = str(self.cb_com_ports.currentText())
        ssid = str(self.cb_ssids.currentText())
        password = str(self.lineedit_wifi_pass.text())
        try:
            # Open connection
            self.ser = serial.Serial(port=com_port, baudrate=115200)
            self.progress_upload.setValue(0)

            # Store SSID
            self.ser.write('set_ssid\n'.encode())
            ret = self.ser.readline().decode('ascii').strip()
            if ret == 'OK':
                self.ser.write(('%s\n' % ssid).encode())
            ret = self.ser.readline().decode('ascii').strip()
            if ret != ssid:
                raise Exception('SSID not successfully written')
            self.progress_upload.setValue(25)

            # Store pass
            self.ser.write('set_pass\n'.encode())
            ret = self.ser.readline().decode('ascii').strip()
            if ret == 'OK':
                self.ser.write(('%s\n' % password).encode())
            ret = self.ser.readline().decode('ascii').strip()
            if ret != password:
                raise Exception('Password not successfully written')
            self.progress_upload.setValue(50)

            # Active new configuration
            self.ser.write('init_wifi\n'.encode())
            self.progress_upload.setValue(75)

            # Wait for node to reconnect
            wifi_status = ''
            while wifi_status != 'OK' and 'E1' not in wifi_status:
                self.ser.write('get_wifi_status\n'.encode())
                wifi_status = self.ser.readline().decode('ascii').strip()
            self.progress_upload.setValue(100)

            # Close connection
            self.ser.close()

            # Update WiFi Status
            self.get_wifi_status()

        except Exception as e:
            print(e)

        finally:
            # Close connection
            self.ser.close()

    def get_wifi_status(self):
        com_port = str(self.cb_com_ports.currentText())
        try:
            # Open connection
            self.ser = serial.Serial(port=com_port, baudrate=115200)
            # Get WiFi status
            self.gb_wifi_status.setEnabled(True)
            # Get available WiFi SSIDs
            self.ser.write('get_wifi_status\n'.encode())
            wifi_status = self.ser.readline().decode('ascii').strip()
            if wifi_status == '3':
                self.label_wifi_status.setText('Connected')
                self.label_wifi_status.setStyleSheet('font-weight: bold; color: green')

                # Get current SSID
                self.ser.write('get_ssid\n'.encode())
                ssid = self.ser.readline().decode('ascii').strip()
                self.label_cur_ssid.setText(ssid)

                # Get current IP
                self.ser.write('get_ip\n'.encode())
                ip = self.ser.readline().decode('ascii').strip()
                self.label_IP.setText(ip)

            else:
                self.label_wifi_status.setText('Not connected')
                self.label_wifi_status.setStyleSheet('font-weight: normal; color: black')
                self.label_cur_ssid.setText('')
                self.label_IP.setText('')

        except Exception as e:
            print(e)

        finally:
            # Close connection
            self.ser.close()

    def connect_button(self):
        com_port = str(self.cb_com_ports.currentText())
        try:
            # Open connection
            self.ser = serial.Serial(port=com_port, baudrate=115200)

            # Get UUID
            self.ser.write('get_uuid\n'.encode())
            uuid = self.ser.readline().decode('ascii').strip()
            self.label_uuid_status.setText(uuid)

            # Get available WiFi SSIDs
            self.ser.write('list_ssid\n'.encode())
            ssid_list = json.loads(self.ser.readline().decode('ascii'))

            for ssid in sorted(ssid_list, reverse=True):
                self.cb_ssids.addItem(ssid)

            # Close connection
            self.ser.close()

            # Get WiFi Status
            self.get_wifi_status()

            # Enable WiFi configuration
            self.gb_wifi.setEnabled(True)

        except Exception as e:
            print(e)

        finally:
            # Close connection
            self.ser.close()


if __name__ == '__main__':
    app = QApplication([])
    app.setStyle('Fusion')
    window = App()
    window.show()
    app.exec_()
