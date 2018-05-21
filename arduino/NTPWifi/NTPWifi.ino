#include <WiFi.h>
#include <WiFiUdp.h>
#include <TimeLib.h>
#include "config.h"

// Defines
#define SEVENTY_YEARS 2208988800UL
#define SECS_PER_HOUR 3600 
#define SECS_PER_DAY 86400
#define SECS_PER_MIN 60
#define DAYS_PER_WEEK 7
#define EPOCH_DAY_OF_WEEK 4                       // 1st of January 1970 was a Thursday

// WiFi settings
int status = WL_IDLE_STATUS;
char ssid[] = WIFI_SSID;      
char pass[] = WIFI_PASSWD;

// UDP settings
unsigned int localPort = 8888;                    // local port to listen for UDP packets
WiFiUDP Udp;                                      // A UDP instance to let us send and receive packets over UDP

// NTP settings
IPAddress timeServerPool;
const int NTP_PACKET_SIZE = 48;                   // NTP time stamp is in the first 48 bytes of the message
byte packetBuffer[ NTP_PACKET_SIZE];              // A buffer to hold incoming and outgoing packets
const unsigned long seventyYears = 2208988800UL;  // Offset between NTP and UNIX time (1 Jan 1900 vs 1970)
const int timeZone = 1;                           // Central European Time

void setup() {
  // Open serial communications and wait for port to open:
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  // check for the presence of the shield:
  if (WiFi.status() == WL_NO_SHIELD) {
    Serial.println("WiFi shield not present");
    // don't continue:
    while (true);
  }

  // attempt to connect to Wifi network:
  while (status != WL_CONNECTED) {
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(ssid);
    // Connect to WPA/WPA2 network. Change this line if using open or WEP network:
    status = WiFi.begin(ssid, pass);

    // wait 10 seconds for connection:
    delay(5000);
  }

  Serial.println("Connected to wifi");
  printWifiStatus();

  // Get NTP NL pool server IP
  WiFi.hostByName("nl.pool.ntp.org", timeServerPool);
  Serial.print("NTP NL pool server IP: ");
  Serial.println(timeServerPool);

  Udp.begin(localPort);
}

void loop() {
  sendNTPpacket(timeServerPool);                // Send an NTP packet to a time server
  delay(1000);                                  // Wait for response

  if(Udp.parsePacket())                         // Parse the UDP packet
  {
    Udp.read(packetBuffer, NTP_PACKET_SIZE);    // Read the packet into the buffer
    unsigned long epoch = readNtpPacket();
    print_time(epoch);
  }

  delay(10000);
}

void print_time(unsigned long epoch) {
  // print the hour, minute and second:
  Serial.print("The UTC time is ");       // UTC is the time at Greenwich Meridian (GMT)
  Serial.print(unix_time('h',epoch));
  Serial.print(':');
  if (unix_time('m',epoch) < 10) {
    // In the first 10 minutes of each hour, we'll want a leading '0'
    Serial.print('0');
  }
  Serial.print(unix_time('m',epoch));
  Serial.print(':');
  if (unix_time('s',epoch) < 10) {
    // In the first 10 seconds of each minute, we'll want a leading '0'
    Serial.print('0');
  }
  Serial.println(unix_time('s',epoch)); // print the second  
}

int unix_time(char mode, unsigned long epoch) {
  switch(mode) {
    case 'h': // Hour
      return (epoch  % SECS_PER_DAY) / SECS_PER_HOUR;
      break;
    case 'm': // Minute
      return (epoch  % SECS_PER_HOUR) / SECS_PER_MIN;
      break;
    case 's': // Second
      return epoch % SECS_PER_MIN;
      break;
    default:
      return 0;  
  }
}

int unix_date(char mode, unsigned long epoch) {
  switch(mode) {
    case 'd': // Day
      return epoch  / SECS_PER_DAY;
      break;
    case 'm': // Month
      return (epoch  % 3600) / 60;
      break;
    case 'y': // Year
      return epoch % 60;
      break;
    case 'w': // Day of week
      return ((epoch / SECS_PER_DAY)+EPOCH_DAY_OF_WEEK) % DAYS_PER_WEEK;
      break;
    default:
      return 0;  
  }   
}

unsigned long readNtpPacket() {
    // The timestamp starts at byte 40 of the received packet and is four bytes (two words) long
    unsigned long highWord = word(packetBuffer[40], packetBuffer[41]);
    unsigned long lowWord = word(packetBuffer[42], packetBuffer[43]);
    
    // Combine the four bytes into a long integer: NTP time (seconds since Jan 1 1900):
    unsigned long secsSince1900 = highWord << 16 | lowWord;

    // Convert NTP time into UNIX time
    return secsSince1900 - SEVENTY_YEARS + timeZone * SECS_PER_HOUR;
}

// send an NTP request to the time server at the given address
unsigned long sendNTPpacket(IPAddress& address) {
  // set all bytes in the buffer to 0
  memset(packetBuffer, 0, NTP_PACKET_SIZE);
  // Initialize values needed to form NTP request
  packetBuffer[0] = 0b11100011;   // LI, Version, Mode
  packetBuffer[1] = 0;            // Stratum, or type of clock
  packetBuffer[2] = 6;            // Polling Interval
  packetBuffer[3] = 0xEC;         // Peer Clock Precision
  // 8 bytes of zero for Root Delay & Root Dispersion
  packetBuffer[12]  = 49;
  packetBuffer[13]  = 0x4E;
  packetBuffer[14]  = 49;
  packetBuffer[15]  = 52;

  // All NTP fields have been given values, now you can send a packet requesting a timestamp:
  Udp.beginPacket(address, 123); //NTP requests are to port 123
  Udp.write(packetBuffer, NTP_PACKET_SIZE);
  Udp.endPacket();
}


void printWifiStatus() {
  // print the SSID of the network you're attached to:
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print your WiFi shield's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);

  // print the received signal strength:
  long rssi = WiFi.RSSI();
  Serial.print("signal strength (RSSI):");
  Serial.print(rssi);
  Serial.println(" dBm");
}










