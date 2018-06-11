#include <WiFi.h>
#include <WiFiUdp.h>
#include <TimeLib.h>
#include "config.h"

// Defines
#define SEVENTY_YEARS 2208988800UL

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
int timeZone = 2;                                 // Central European Time with DTS (GMT+2)

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

  // Start UDP communication
  Udp.begin(localPort);

  // Initialize time and DTS
  unsigned long epoch = readNtpPacket();        // Read an NTP packet from a time server
  epoch = checkDts(epoch);
  setTime(epoch);
}

void loop() {
  cron(now()); 
}

void print_time(unsigned long t) {
  // print the hour, minute and second:
  Serial.print("The UTC time is ");       // UTC is the time at Greenwich Meridian (GMT)
  Serial.print(hour(t));
  Serial.print(':');
  if (minute(t) < 10) {
    // In the first 10 minutes of each hour, we'll want a leading '0'
    Serial.print('0');
  }
  Serial.print(minute(t));
  Serial.print(':');
  if (second(t) < 10) {
    // In the first 10 seconds of each minute, we'll want a leading '0'
    Serial.print('0');
  }
  Serial.println(second(t)); // print the second  

  Serial.print("The UTC date is ");
  if (day(t) < 10) {
    // In the first 10 minutes of each hour, we'll want a leading '0'
    Serial.print('0');
  }
  Serial.print(day(t));
  Serial.print('-');
  if (month(t) < 10) {
    // In the first 10 seconds of each minute, we'll want a leading '0'
    Serial.print('0');
  }
  Serial.print(month(t)); // print the second    
  Serial.print('-');
  Serial.println(year(t));
}

void cron(unsigned long t) {
  // m h dom m dow command

  // Cron run timer
  unsigned long tStart = millis();
  
  // 0 2 * * 0 Check for DTS update every Sunday at 02:00
  if((weekday(t)==1) and (hour(t)==2) and (minute(t)==0) and (second(t) == 0)) {
    checkDts(t);
  }

  // 0 0 * * * Sync with NTP server every day at 00:00
  if((minute(t)==0) and (second(t) == 0)) { //(hour(t)==0) and 
    print_time(now());
    Serial.println("NTP resync");
    t = readNtpPacket();        // Read an NTP packet from a time server
    setTime(t);
    print_time(now());    
  }

  // * * * * * Print time to serial port every minute
  if(second(t) == 0) {
    print_time(now());
  }

  // Only execute commands once every second
  if((millis() - tStart) < 1000) {
    delay(1000);
  }
}

unsigned long checkDts(unsigned long t) {
  if((month(t) > 3) or (month(t) < 10)) {   // Summer time from end of March to end of October
    return t;
  }
  if((month(t) == 3) and (day(t) >= 25)) {  // Check for last Sunday in March
    if((day(t) - weekday(t)) >= 24) {       // Last Sunday of March has passed
      return t;
    }
  }
  if((month(t) == 10) and (day(t) >= 25)) { // Check for last Sunday in October
    if((day(t) - weekday(t)) < 24) {        // Last Sunday of October has not passed
      return t;
    }  
  }

  timeZone = 1;                             // Winter time: GMT+1
  return (t - SECS_PER_HOUR); 
}

unsigned long readNtpPacket() {
  // Send an NTP packet to a time server
  sendNTPpacket(timeServerPool);                
  delay(2000);

  if(Udp.parsePacket()) {
    // Read the packet into the buffer
    Udp.read(packetBuffer, NTP_PACKET_SIZE);    

    // The timestamp starts at byte 40 of the received packet and is four bytes (two words) long
    unsigned long highWord = word(packetBuffer[40], packetBuffer[41]);
    unsigned long lowWord = word(packetBuffer[42], packetBuffer[43]);
    
    // Combine the four bytes into a long integer: NTP time (seconds since Jan 1 1900):
    unsigned long secsSince1900 = highWord << 16 | lowWord;

    // Convert NTP time into UNIX time
    return secsSince1900 - SEVENTY_YEARS + timeZone * SECS_PER_HOUR;
  }
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










